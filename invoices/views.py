from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from products.models import Product

from .forms import InvoiceForm, InvoiceItemFormSet
from .models import Invoice, InvoiceItem


def _is_admin(user):
    return user.is_staff


@login_required
def invoice_list(request):
    status_filter = request.GET.get("status", "all")
    invoices_qs = Invoice.objects.select_related("customer").order_by(
        "-invoice_date", "-id"
    )
    if status_filter == "paid":
        invoices_qs = invoices_qs.filter(status="paid")
    elif status_filter == "pending":
        invoices_qs = invoices_qs.filter(status__in=["unpaid", "partial"])

    return render(
        request,
        "invoices/invoice_list.html",
        {
            "invoices": invoices_qs,
            "status_filter": status_filter,
        },
    )


@login_required
@transaction.atomic
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.status = "unpaid"
            invoice.subtotal = Decimal("0.00")
            invoice.tax_amount = Decimal("0.00")
            invoice.total_amount = Decimal("0.00")
            invoice.save()

            subtotal = Decimal("0.00")
            tax_amount = Decimal("0.00")

            for item_form in formset:
                if not item_form.cleaned_data:
                    continue
                product = item_form.cleaned_data.get("product")
                quantity = item_form.cleaned_data.get("quantity") or 0
                if not product or quantity <= 0:
                    continue

                # Fetch current product pricing and GST
                product_ref = Product.objects.get(pk=product.pk)
                price = product_ref.price
                gst_rate = product_ref.gst_rate

                line_subtotal = price * quantity
                line_tax = (line_subtotal * gst_rate) / Decimal("100")
                line_total = line_subtotal + line_tax

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product_ref,
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
    else:
        form = InvoiceForm(initial={"invoice_date": timezone.now().date()})
        formset = InvoiceItemFormSet()

    return render(
        request,
        "invoices/invoice_form.html",
        {
            "form": form,
            "formset": formset,
        },
    )


@login_required
@user_passes_test(_is_admin)
def invoice_pdf(request, pk):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return HttpResponse(
            "ReportLab is not installed. Please install it with 'pip install reportlab'.",
            content_type="text/plain",
        )

    invoice = get_object_or_404(Invoice, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Billing Management System")
    y -= 30

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Invoice Number: {invoice.invoice_number}")
    y -= 15
    p.drawString(50, y, f"Invoice Date: {invoice.invoice_date}")
    y -= 15
    p.drawString(50, y, f"Customer: {invoice.customer.name}")
    y -= 25

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Items")
    y -= 20

    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Product")
    p.drawString(220, y, "Qty")
    p.drawString(270, y, "Price")
    p.drawString(340, y, "GST %")
    p.drawString(400, y, "Total")
    y -= 15

    for item in invoice.items.select_related("product").all():
        if y < 80:
            p.showPage()
            y = height - 50
        p.drawString(50, y, item.product.name[:25])
        p.drawString(220, y, str(item.quantity))
        p.drawString(270, y, f"{item.price:.2f}")
        p.drawString(340, y, f"{item.gst_rate:.2f}")
        p.drawString(400, y, f"{item.total:.2f}")
        y -= 15

    y -= 20
    p.setFont("Helvetica-Bold", 11)
    p.drawString(300, y, f"Subtotal: {invoice.subtotal:.2f}")
    y -= 15
    p.drawString(300, y, f"Tax: {invoice.tax_amount:.2f}")
    y -= 15
    p.drawString(300, y, f"Total: {invoice.total_amount:.2f}")

    p.showPage()
    p.save()
    return response


