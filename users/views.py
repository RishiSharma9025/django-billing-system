from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import BusinessRegistrationRequestForm


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        return redirect(reverse("dashboard:home"))

    if request.method == "GET":
        # Login happens via modal on landing page
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "user")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if role == "admin":
                return redirect("/admin/")
            return redirect(reverse("dashboard:home"))

        messages.error(request, "Invalid username or password.")

    return redirect("/")


def logout_view(request):
    logout(request)
    return redirect("/login/")


def register_business(request):
    if request.user.is_authenticated:
        return redirect(reverse("dashboard:home"))

    if request.method == "POST":
        form = BusinessRegistrationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your request has been submitted. Admin will review your business details.",
            )
            return redirect("/")
    else:
        form = BusinessRegistrationRequestForm()

    return render(request, "users/register_business.html", {"form": form})
