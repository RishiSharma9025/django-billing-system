from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "gst_number", "created_at")
    search_fields = ("name", "phone", "email", "gst_number")
    list_filter = ("created_at",)
