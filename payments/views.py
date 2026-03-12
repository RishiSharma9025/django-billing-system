from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from invoices.models import Invoice
from payments.models import Payment

from .forms import PaymentForm


@login_required
def payment_list(request):
    payments = (
        Payment.objects.select_related("invoice", "invoice__customer")
        .order_by("-payment_date", "-id")
    )
    return render(request, "payments/payment_list.html", {"payments": payments})


@login_required
def payment_add(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("payments:list")
    else:
        form = PaymentForm(initial={"payment_date": timezone.now().date()})

    return render(request, "payments/payment_add.html", {"form": form})


@login_required
def payment_history(request, invoice_id: int):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    payments = invoice.payments.all()
    total_paid = payments.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    remaining = invoice.total_amount - total_paid

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            return redirect("payments:history", invoice_id=invoice.id)
    else:
        form = PaymentForm(initial={"payment_date": timezone.now().date()})

    return render(
        request,
        "payments/payment_form.html",
        {
            "invoice": invoice,
            "payments": payments,
            "total_paid": total_paid,
            "remaining": remaining,
            "form": form,
        },
    )

