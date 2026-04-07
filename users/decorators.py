from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse

from .models import Business
from .utils import get_owner_business, is_staff_or_superuser


def approved_business_required(view_func):
    """
    Use after @login_required. Staff/superuser: pass. Owners: must have Approved business and active account.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        user = request.user
        if is_staff_or_superuser(user):
            return view_func(request, *args, **kwargs)

        biz = get_owner_business(user)
        if not biz:
            messages.error(
                request,
                "No business profile is linked to your account. Contact admin.",
            )
            return redirect(reverse("landing"))

        if biz.status == Business.Status.REJECTED:
            messages.error(
                request,
                "Your business registration was not approved. Contact admin.",
            )
            return redirect(reverse("landing"))

        if biz.status != Business.Status.APPROVED or not user.is_active:
            messages.error(
                request,
                "Your business registration is awaiting approval from admin.",
            )
            return redirect(reverse("landing"))

        return view_func(request, *args, **kwargs)

    return _wrapped
