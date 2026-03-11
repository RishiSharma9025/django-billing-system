from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "payment_date", "amount_paid", "payment_method")
    search_fields = ("invoice__invoice_number",)
    list_filter = ("payment_method", "payment_date")

