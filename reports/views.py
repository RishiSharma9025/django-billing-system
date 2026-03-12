import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils.dateparse import parse_date

from customers.models import Customer
from invoices.models import Invoice, InvoiceItem


def _parse_range(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None
    if start and end and start > end:
        start, end = end, start
    return start, end


@login_required
def index(request):
    start, end = _parse_range(request)

    invoices = Invoice.objects.select_related("customer").all()
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

    sales_by_customer = (
        invoices.values("customer__name")
        .annotate(total=Sum("total_amount"), invoices=Count("id"))
        .order_by("-total")[:20]
    )

    items = InvoiceItem.objects.select_related("product", "invoice")
    if start:
        items = items.filter(invoice__invoice_date__gte=start)
    if end:
        items = items.filter(invoice__invoice_date__lte=end)

    product_sales = (
        items.values("product__name")
        .annotate(
            quantity=Sum("quantity"),
            # InvoiceItem already stores row total, so we can safely sum it.
            revenue=Sum("total", output_field=DecimalField(max_digits=12, decimal_places=2)),
        )
        .order_by("-revenue")[:20]
    )

    # Customer revenue: total invoices + total paid (from invoice payments)
    customers = Customer.objects.all()
    if start:
        customers = customers.filter(invoices__invoice_date__gte=start).distinct()
    if end:
        customers = customers.filter(invoices__invoice_date__lte=end).distinct()

    customer_revenue = (
        Customer.objects.values("name")
        .annotate(
            total_invoices=Count("invoices", distinct=True),
            total_billed=Sum("invoices__total_amount"),
            total_paid=Sum("invoices__payments__amount_paid"),
        )
        .order_by("-total_paid")[:20]
    )

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
        "today": date.today(),
    }
    return render(request, "reports/index.html", context)

