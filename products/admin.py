from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "gst_rate", "stock_quantity", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active",)
