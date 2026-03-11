from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        return redirect(reverse("dashboard:home"))

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

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/login/")
