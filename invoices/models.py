from django.db import models
from django.utils import timezone

from customers.models import Customer
from products.models import Product


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("unpaid", "Unpaid"),
        ("partial", "Partially Paid"),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")
    invoice_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="unpaid")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-invoice_date", "-id"]

    @staticmethod
    def generate_invoice_number() -> str:
        today_str = timezone.now().strftime("%Y%m%d")
        prefix = f"INV{today_str}"
        last_invoice = (
            Invoice.objects.filter(invoice_number__startswith=prefix)
            .order_by("-id")
            .first()
        )
        sequence = 1
        if last_invoice and "-" in last_invoice.invoice_number:
            try:
                sequence = int(last_invoice.invoice_number.split("-")[-1]) + 1
            except ValueError:
                sequence = 1
        return f"{prefix}-{sequence:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} - {self.customer.name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="invoice_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="GST percentage")
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity} ({self.invoice.invoice_number})"

