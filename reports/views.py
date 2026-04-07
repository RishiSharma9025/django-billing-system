import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils.dateparse import parse_date

from customers.models import Customer
from invoices.models import Invoice, InvoiceItem
from payments.models import Payment
from users.decorators import approved_business_required
from users.utils import queryset_for_business
from ai_features.forecasting import forecast_revenue
from ai_features.ocr import extract_invoice_text


def _parse_range(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None
    if start and end and start > end:
        start, end = end, start
    return start, end


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

    extracted_ocr_text = ""
    if request.method == "POST" and request.FILES.get("invoice_image"):
        up = request.FILES["invoice_image"]
        from django.core.files.storage import default_storage

        tmp_path = default_storage.save(f"tmp/{up.name}", up)
        full_path = default_storage.path(tmp_path)
        extracted_ocr_text = extract_invoice_text(full_path)

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
    }
    return render(request, "reports/index.html", context)
