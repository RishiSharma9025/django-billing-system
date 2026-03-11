from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ("product", "quantity", "price", "gst_rate", "total")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer",
        "invoice_date",
        "subtotal",
        "tax_amount",
        "total_amount",
        "status",
    )
    search_fields = ("invoice_number", "customer__name", "customer__phone", "customer__email")
    list_filter = ("status", "invoice_date")
    date_hierarchy = "invoice_date"
    inlines = [InvoiceItemInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "product", "quantity", "price", "gst_rate", "total")
    search_fields = ("invoice__invoice_number", "product__name")

