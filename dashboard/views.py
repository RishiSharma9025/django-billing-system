from decimal import Decimal
import json
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from customers.models import Customer
from invoices.models import Invoice, InvoiceItem
from payments.models import Payment
from products.models import Product
from users.decorators import approved_business_required
from users.models import Business
from users.utils import queryset_for_business
from ai_features.anomaly import detect_invoice_anomalies
from ai_features.forecasting import forecast_revenue
from ai_features.recommendations import recommend_products
from ai_features.segmentation import segment_customers


@ensure_csrf_cookie
def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return render(request, "dashboard.html")


def about_page(request):
    return render(request, "site/about.html")


def contact_page(request):
    return render(request, "site/contact.html")


def privacy_page(request):
    return render(request, "site/privacy.html")


def terms_page(request):
    return render(request, "site/terms.html")


def help_page(request):
    return render(request, "site/help.html")


@login_required
@approved_business_required
def home(request):
    customers_qs = queryset_for_business(Customer.objects.all(), request.user)
    products_qs = queryset_for_business(Product.objects.all(), request.user)
    invoices_qs = queryset_for_business(Invoice.objects.all(), request.user)

    total_customers = customers_qs.count()
    total_products = products_qs.count()
    total_invoices = invoices_qs.count()
    total_revenue = (
        invoices_qs.filter(status="paid").aggregate(total=Sum("total_amount"))["total"]
        or 0
    )
    unpaid_invoices = invoices_qs.filter(status__in=["unpaid", "partial"]).count()
    recent_invoices = invoices_qs.select_related("customer").order_by(
        "-invoice_date", "-id"
    )[:5]

    monthly_qs = (
        invoices_qs.annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(
            total_sales=Sum("total_amount"),
            invoice_count=Count("id"),
        )
        .order_by("month")
    )

    monthly_labels = []
    monthly_sales = []
    monthly_invoice_counts = []
    for row in monthly_qs:
        month = row["month"]
        if month is None:
            continue
        monthly_labels.append(month.strftime("%Y-%m"))
        monthly_sales.append(float(row["total_sales"] or 0))
        monthly_invoice_counts.append(int(row["invoice_count"] or 0))

    status_counts_qs = (
        invoices_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_labels = []
    status_counts = []
    for row in status_counts_qs:
        label = dict(Invoice.STATUS_CHOICES).get(row["status"], row["status"])
        status_labels.append(label)
        status_counts.append(int(row["count"] or 0))

    payments_qs = queryset_for_business(
        Payment.objects.all(),
        request.user,
        business_field="invoice__business",
    )
    recent_customers = customers_qs.order_by("-created_at")[:5]
    recent_payments = payments_qs.select_related("invoice").order_by(
        "-payment_date", "-id"
    )[:5]

    forecast_values = forecast_revenue(monthly_sales, periods=3)
    segments = segment_customers(
        [
            {"name": c.get("name"), "total_paid": float(c.get("total_paid") or 0)}
            for c in queryset_for_business(Customer.objects.all(), request.user)
            .values("name")
            .annotate(total_paid=Sum("invoices__payments__amount_paid"))[:100]
        ]
    )
    recommendation_pairs = recommend_products(
        list(
            queryset_for_business(
                InvoiceItem.objects.select_related("invoice", "product"),
                request.user,
                business_field="invoice__business",
            ).values_list("invoice_id", "product__name")[:300]
        )
    )
    anomaly_summary = detect_invoice_anomalies(
        list(invoices_qs.values_list("total_amount", flat=True)[:500])
    )

    context = {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_invoices": total_invoices,
        "total_revenue": total_revenue,
        "unpaid_invoices": unpaid_invoices,
        "recent_invoices": recent_invoices,
        "recent_customers": recent_customers,
        "recent_payments": recent_payments,
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_sales_json": json.dumps(monthly_sales),
        "monthly_invoice_counts_json": json.dumps(monthly_invoice_counts),
        "status_labels_json": json.dumps(status_labels),
        "status_counts_json": json.dumps(status_counts),
        "ai_forecast_values_json": json.dumps(forecast_values),
        "ai_segments": segments,
        "ai_recommendations": recommendation_pairs,
        "ai_anomaly_count": anomaly_summary.get("anomaly_count", 0),
    }

    return render(request, "dashboard/home.html", context)


def _is_admin(user):
    return user.is_staff


@login_required
@approved_business_required
@user_passes_test(_is_admin)
def generate_demo_data(request):
    if request.method != "POST":
        return redirect("dashboard:home")

    biz = Business.objects.filter(status=Business.Status.APPROVED).first()
    if not biz:
        # Let admins test quickly without manually creating/approving a business first.
        biz = Business.objects.create(
            owner=request.user,
            business_name="Demo Business",
            business_type="Demo",
            status=Business.Status.APPROVED,
        )

    for i in range(10):
        Customer.objects.get_or_create(
            business=biz,
            name=f"Customer {i+1}",
            defaults={
                "phone": f"99999{i:05d}",
                "email": f"customer{i+1}@example.com",
                "address": "Demo address",
                "gst_number": "",
            },
        )

    for i in range(10):
        Product.objects.get_or_create(
            business=biz,
            name=f"Product {i+1}",
            defaults={
                "description": "Demo product",
                "price": Decimal("100.00") + i,
                "gst_rate": Decimal("18.00"),
                "stock_quantity": 100,
                "is_active": True,
            },
        )

    customers = list(Customer.objects.filter(business=biz))
    products = list(Product.objects.filter(business=biz, is_active=True))

    for _ in range(20):
        if not customers or not products:
            break
        customer = random.choice(customers)
        invoice = Invoice.objects.create(
            business=biz,
            customer=customer,
            invoice_date=timezone.now().date(),
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            status="unpaid",
        )
        line_count = random.randint(1, 3)
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        for _ in range(line_count):
            product = random.choice(products)
            quantity = random.randint(1, 5)
            price = product.price
            gst_rate = product.gst_rate
            line_subtotal = price * quantity
            line_tax = (line_subtotal * gst_rate) / Decimal("100")
            line_total = line_subtotal + line_tax
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                price=price,
                gst_rate=gst_rate,
                total=line_total,
            )
            subtotal += line_subtotal
            tax_amount += line_tax
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = subtotal + tax_amount
        invoice.save()

    messages.success(request, "Demo data generated.")
    return redirect("dashboard:home")
