from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from invoices.models import Invoice
from users.decorators import approved_business_required
from users.utils import get_owner_business, is_staff_or_superuser, queryset_for_business

from .forms import PaymentForm, PaymentRecordForm
from .models import Payment


def _payment_business(request):
    if is_staff_or_superuser(request.user):
        return None
    return get_owner_business(request.user)


@login_required
@approved_business_required
def payment_list(request):
    payments = queryset_for_business(
        Payment.objects.select_related("invoice", "invoice__customer"),
        request.user,
        business_field="invoice__business",
    ).order_by("-payment_date", "-id")
    return render(request, "payments/payment_list.html", {"payments": payments})


@login_required
@approved_business_required
def payment_add(request):
    business = _payment_business(request)
    if request.method == "POST":
        form = PaymentForm(request.POST, business=business)
        if form.is_valid():
            form.save()
            return redirect("payments:list")
    else:
        form = PaymentForm(initial={"payment_date": timezone.now().date()}, business=business)

    return render(request, "payments/payment_add.html", {"form": form})


@login_required
@approved_business_required
def payment_history(request, invoice_id: int):
    inv_qs = queryset_for_business(Invoice.objects.all(), request.user)
    invoice = get_object_or_404(inv_qs, pk=invoice_id)
    payments = invoice.payments.all()
    total_paid = payments.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    remaining = invoice.total_amount - total_paid

    if request.method == "POST":
        form = PaymentRecordForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            return redirect("payments:history", invoice_id=invoice.id)
    else:
        form = PaymentRecordForm(initial={"payment_date": timezone.now().date()})

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
