from decimal import Decimal
import json
import random

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from customers.models import Customer
from invoices.models import Invoice, InvoiceItem
from payments.models import Payment
from products.models import Product


@login_required
def home(request):
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_invoices = Invoice.objects.count()
    total_revenue = (
        Invoice.objects.filter(status="paid").aggregate(total=Sum("total_amount"))[
            "total"
        ]
        or 0
    )
    unpaid_invoices = Invoice.objects.filter(status__in=["unpaid", "partial"]).count()
    recent_invoices = Invoice.objects.select_related("customer").order_by(
        "-invoice_date", "-id"
    )[:5]

    # Monthly sales and invoice counts (safe even if no data)
    monthly_qs = (
        Invoice.objects.annotate(month=TruncMonth("invoice_date"))
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

    # Payment status distribution based on invoice status
    status_counts_qs = (
        Invoice.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_labels = []
    status_counts = []
    for row in status_counts_qs:
        label = dict(Invoice.STATUS_CHOICES).get(row["status"], row["status"])
        status_labels.append(label)
        status_counts.append(int(row["count"] or 0))

    # Recent activity (simple demo: latest customers, invoices, payments)
    recent_customers = Customer.objects.order_by("-created_at")[:5]
    recent_payments = Payment.objects.select_related("invoice").order_by(
        "-payment_date", "-id"
    )[:5]

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
    }

    return render(request, "dashboard/home.html", context)


def _is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(_is_admin)
def generate_demo_data(request):
    if request.method != "POST":
        return redirect("dashboard:home")

    # Simple demo data generator
    for i in range(10):
        Customer.objects.get_or_create(
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
            name=f"Product {i+1}",
            defaults={
                "description": "Demo product",
                "price": Decimal("100.00") + i,
                "gst_rate": Decimal("18.00"),
                "stock_quantity": 100,
                "is_active": True,
            },
        )

    customers = list(Customer.objects.all())
    products = list(Product.objects.filter(is_active=True))

    for _ in range(20):
        if not customers or not products:
            break
        customer = random.choice(customers)
        invoice = Invoice.objects.create(
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

    return redirect("dashboard:home")

