from django.contrib import admin

from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "owner",
        "status",
        "phone",
        "email",
        "gst_number",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "business_name",
        "owner__username",
        "owner__email",
        "phone",
        "email",
        "gst_number",
        "city",
        "state",
        "pincode",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected businesses (activate owners)")
    def approve_selected(self, request, queryset):
        updated = 0
        for business in queryset.select_related("owner"):
            business.status = Business.Status.APPROVED
            business.save(update_fields=["status"])
            owner = business.owner
            if not owner.is_active:
                owner.is_active = True
                owner.save(update_fields=["is_active"])
            updated += 1
        self.message_user(request, f"Approved {updated} business(es).")

    @admin.action(description="Reject selected businesses (owners stay inactive)")
    def reject_selected(self, request, queryset):
        count = queryset.update(status=Business.Status.REJECTED)
        self.message_user(request, f"Rejected {count} business(es).")
