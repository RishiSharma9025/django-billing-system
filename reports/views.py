import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from ai_features.forecasting import forecast_revenue
from ai_features.ocr import extract_invoice_text
from ai_features.receipt_parse import parse_receipt_structured
from customers.models import Customer
from invoices.models import Invoice, InvoiceItem
from products.models import Product
from users.decorators import approved_business_required
from users.models import Business
from users.utils import get_owner_business, is_staff_or_superuser, queryset_for_business

RECEIPT_SESSION_KEY = "receipt_invoice_draft"


def _parse_range(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None
    if start and end and start > end:
        start, end = end, start
    return start, end


def _business_for_receipt(user):
    b = get_owner_business(user)
    if b:
        return b
    if is_staff_or_superuser(user):
        return Business.objects.filter(status=Business.Status.APPROVED).order_by("-id").first()
    return None


def _match_product(business, name_hint: str):
    if not business or not (name_hint or "").strip():
        return None
    hint = name_hint.strip().lower()
    qs = Product.objects.filter(business=business, is_active=True)
    exact = qs.filter(name__iexact=name_hint.strip()).first()
    if exact:
        return exact
    best = None
    for p in qs:
        pn = p.name.lower()
        if hint in pn or pn in hint:
            best = p
            break
    return best


@login_required
@approved_business_required
def index(request):
    start, end = _parse_range(request)

    invoices = queryset_for_business(
        Invoice.objects.select_related("customer").all(),
        request.user,
    )
    if start:
        invoices = invoices.filter(invoice_date__gte=start)
    if end:
        invoices = invoices.filter(invoice_date__lte=end)

    total_sales = invoices.aggregate(total=Sum("total_amount"))["total"] or 0

    status_counts = (
        invoices.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_labels = [row["status"].title() for row in status_counts]
    status_values = [row["count"] for row in status_counts]

    monthly = (
        invoices.annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )
    month_labels = [row["month"].strftime("%b %Y") for row in monthly if row["month"]]
    month_totals = [float(row["total"] or 0) for row in monthly if row["month"]]
    forecast_totals = forecast_revenue(month_totals, periods=3)

    sales_by_customer = (
        invoices.values("customer__name")
        .annotate(total=Sum("total_amount"), invoices=Count("id"))
        .order_by("-total")[:20]
    )

    items = queryset_for_business(
        InvoiceItem.objects.select_related("product", "invoice"),
        request.user,
        business_field="invoice__business",
    )
    if start:
        items = items.filter(invoice__invoice_date__gte=start)
    if end:
        items = items.filter(invoice__invoice_date__lte=end)

    product_sales = (
        items.values("product__name")
        .annotate(
            quantity=Sum("quantity"),
            revenue=Sum("total", output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
        .order_by("-revenue")[:20]
    )

    customer_revenue = (
        queryset_for_business(Customer.objects.all(), request.user)
        .values("name")
        .annotate(
            total_invoices=Count("invoices", distinct=True),
            total_billed=Sum("invoices__total_amount"),
            total_paid=Sum("invoices__payments__amount_paid"),
        )
        .order_by("-total_paid")[:20]
    )

    business = _business_for_receipt(request.user)
    receipt_customers = (
        Customer.objects.filter(business=business).order_by("name")
        if business
        else Customer.objects.none()
    )
    receipt_products = (
        Product.objects.filter(business=business, is_active=True).order_by("name")
        if business
        else Product.objects.none()
    )

    extracted_ocr_text = ""
    receipt_draft = request.session.get(RECEIPT_SESSION_KEY)

    if request.method == "POST":
        act = request.POST.get("action")

        if act == "extract_receipt" and request.FILES.get("invoice_image"):
            if not business:
                messages.error(request, "No business profile for receipt import.")
            else:
                up = request.FILES["invoice_image"]
                from django.core.files.storage import default_storage

                tmp_path = default_storage.save(f"tmp/{up.name}", up)
                full_path = default_storage.path(tmp_path)
                try:
                    extracted_ocr_text = extract_invoice_text(full_path)
                    parsed = parse_receipt_structured(extracted_ocr_text)

                    lines = []
                    for it in parsed.get("items") or []:
                        nm = it.get("name") or ""
                        pid = _match_product(business, nm)
                        lines.append(
                            {
                                "name_hint": nm[:200],
                                "quantity": int(it.get("quantity") or 1),
                                "unit_price": str(it.get("unit_price") or "0"),
                                "matched_product_id": pid.pk if pid else None,
                            }
                        )

                    request.session[RECEIPT_SESSION_KEY] = {
                        "ocr_text": extracted_ocr_text,
                        "parsed_total": parsed.get("total") or "",
                        "lines": lines,
                    }
                    request.session.modified = True
                    messages.success(
                        request,
                        "Text extracted. Review line items and customer, then create the invoice.",
                    )
                    return redirect("reports:index")
                finally:
                    try:
                        default_storage.delete(tmp_path)
                    except Exception:
                        pass

        elif act == "discard_receipt":
            request.session.pop(RECEIPT_SESSION_KEY, None)
            messages.info(request, "Receipt draft cleared.")
            return redirect("reports:index")

        elif act == "create_invoice_from_receipt":
            receipt_draft = request.session.get(RECEIPT_SESSION_KEY)
            if not business or not receipt_draft:
                messages.error(request, "Nothing to import.")
                return redirect("reports:index")
            try:
                _create_invoice_from_receipt_post(request, business, receipt_draft)
                return redirect("invoices:invoice_list")
            except (ValueError, InvalidOperation, Product.DoesNotExist, Customer.DoesNotExist) as e:
                messages.error(request, f"Could not create invoice: {e}")
                return redirect("reports:index")

    if receipt_draft and not extracted_ocr_text:
        extracted_ocr_text = receipt_draft.get("ocr_text", "")

    context = {
        "start": start or "",
        "end": end or "",
        "total_sales": total_sales,
        "sales_by_customer": sales_by_customer,
        "product_sales": product_sales,
        "customer_revenue": customer_revenue,
        "chart_status_labels": json.dumps(status_labels),
        "chart_status_values": json.dumps(status_values),
        "chart_month_labels": json.dumps(month_labels),
        "chart_month_values": json.dumps(month_totals),
        "chart_forecast_values": json.dumps(forecast_totals),
        "today": date.today(),
        "ocr_text": extracted_ocr_text,
        "receipt_draft": receipt_draft,
        "receipt_customers": receipt_customers,
        "receipt_products": receipt_products,
        "receipt_business": business,
    }
    return render(request, "reports/index.html", context)


@transaction.atomic
def _create_invoice_from_receipt_post(request, business, draft):
    customer_id = request.POST.get("customer_id")
    inv_date_raw = request.POST.get("invoice_date")
    if not customer_id or not inv_date_raw:
        raise ValueError("Customer and invoice date are required.")
    customer = get_object_or_404(Customer, pk=customer_id, business=business)
    invoice_date = parse_date(inv_date_raw)
    if not invoice_date:
        raise ValueError("Invalid invoice date.")

    invoice = Invoice(
        business=business,
        customer=customer,
        invoice_date=invoice_date,
        subtotal=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        status="unpaid",
        invoice_number="",
    )
    invoice.save()

    subtotal = Decimal("0.00")
    tax_amount = Decimal("0.00")
    lines = draft.get("lines") or []
    any_item = False
    for i in range(len(lines)):
        if request.POST.get(f"include_{i}") != "on":
            continue
        pid = request.POST.get(f"product_{i}")
        qty_raw = request.POST.get(f"qty_{i}", "1")
        if not pid:
            continue
        qty = int(qty_raw)
        if qty < 1:
            continue

        product = Product.objects.get(pk=int(pid), business=business)
        price = product.price
        gst_rate = product.gst_rate
        line_subtotal = price * qty
        line_tax = (line_subtotal * gst_rate) / Decimal("100")
        line_total = line_subtotal + line_tax

        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            quantity=qty,
            price=price,
            gst_rate=gst_rate,
            total=line_total,
        )
        subtotal += line_subtotal
        tax_amount += line_tax
        any_item = True

    if not any_item:
        invoice.delete()
        raise ValueError("Select at least one line item with a product.")

    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total_amount = subtotal + tax_amount
    invoice.save()

    request.session.pop(RECEIPT_SESSION_KEY, None)
    messages.success(
        request,
        f"Invoice {invoice.invoice_number} created from receipt.",
    )
