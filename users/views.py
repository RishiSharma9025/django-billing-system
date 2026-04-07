from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import BusinessOwnerRegistrationForm
from .models import Business


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        return redirect(reverse("dashboard:home"))

    if request.method == "GET":
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "user")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("/")

        # Superuser: full access (admin / dashboard)
        if user.is_superuser:
            login(request, user)
            if role == "admin":
                return redirect("/admin/")
            return redirect(reverse("dashboard:home"))

        # Staff (non-superuser): Django admin + dashboard without business check
        if user.is_staff:
            login(request, user)
            if role == "admin":
                return redirect("/admin/")
            return redirect(reverse("dashboard:home"))

        # Business owners
        biz = user.businesses.order_by("-id").first()

        if biz and biz.status == Business.Status.REJECTED:
            messages.error(
                request,
                "Your business registration was not approved. Contact admin.",
            )
            return redirect("/")

        if not user.is_active or not biz or biz.status != Business.Status.APPROVED:
            messages.error(
                request,
                "Your business registration is awaiting approval from admin.",
            )
            return redirect("/")

        login(request, user)
        if role == "admin":
            messages.info(
                request,
                "Admin panel login requires a staff account. Use your dashboard as a business user.",
            )
            return redirect(reverse("dashboard:home"))
        return redirect(reverse("dashboard:home"))

    return redirect("/")


def logout_view(request):
    logout(request)
    return redirect("/login/")


@ensure_csrf_cookie
def register_business(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard:home"))

    if request.method == "POST":
        form = BusinessOwnerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registration successful. Your business is under review by admin.",
            )
            return redirect("/")
    else:
        form = BusinessOwnerRegistrationForm()

    return render(request, "users/register_business.html", {"form": form})
