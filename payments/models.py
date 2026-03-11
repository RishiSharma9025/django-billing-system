from decimal import Decimal

from django.db import models
from django.db.models import Sum

from invoices.models import Invoice


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("upi", "UPI"),
        ("bank_transfer", "Bank Transfer"),
        ("other", "Other"),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self) -> str:
        return f"Payment {self.amount_paid} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_invoice_status()

    def update_invoice_status(self):
        invoice = self.invoice
        total_paid = (
            invoice.payments.aggregate(total=Sum("amount_paid"))["total"]
            or Decimal("0.00")
        )
        if total_paid <= Decimal("0.00"):
            invoice.status = "unpaid"
        elif total_paid >= invoice.total_amount:
            invoice.status = "paid"
        else:
            invoice.status = "partial"
        invoice.save(update_fields=["status"])

