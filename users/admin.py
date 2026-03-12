from django.contrib import admin

from django.contrib.auth.models import User
from django.utils import timezone

from .models import Business, BusinessRegistrationRequest


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner", "phone", "email", "gst_number", "created_at")
    search_fields = ("business_name", "owner__username", "owner__email", "phone", "gst_number")


@admin.register(BusinessRegistrationRequest)
class BusinessRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("business_name", "full_name", "email", "phone", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("full_name", "email", "phone", "business_name", "gst_number", "city", "state", "pincode")
    readonly_fields = ("created_at", "approved_at", "approved_by")
    actions = ("approve_requests",)

    @admin.action(description="Approve selected requests (create user + business)")
    def approve_requests(self, request, queryset):
        pending = queryset.filter(approved=False)
        for req in pending:
            username_base = (req.email.split("@")[0] or req.full_name.split(" ")[0]).strip().lower()
            username = username_base[:20] or f"user{req.id}"
            # Ensure unique username
            suffix = 1
            while User.objects.filter(username=username).exists():
                suffix += 1
                username = f"{username_base[:16]}{suffix}"

            temp_password = User.objects.make_random_password(length=10)
            user = User.objects.create_user(
                username=username,
                email=req.email,
                password=temp_password,
                first_name=req.full_name.split(" ")[0][:150],
            )

            Business.objects.create(
                owner=user,
                business_name=req.business_name,
                business_type=req.business_type,
                gst_number=req.gst_number,
                phone=req.phone,
                email=req.email,
                address=req.business_address,
                city=req.city,
                state=req.state,
                pincode=req.pincode,
            )

            req.approved = True
            req.approved_by = request.user
            req.approved_at = timezone.now()
            req.save(update_fields=["approved", "approved_by", "approved_at"])

        self.message_user(request, f"Approved {pending.count()} request(s).")
