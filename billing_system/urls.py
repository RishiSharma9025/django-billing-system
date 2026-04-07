"""
URL configuration for billing_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users.views import login_view, logout_view
from dashboard.views import (
    landing,
    about_page,
    contact_page,
    privacy_page,
    terms_page,
    help_page,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/", include("users.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("customers/", include("customers.urls")),
    path("products/", include("products.urls")),
    path("invoices/", include("invoices.urls")),
    path("payments/", include("payments.urls")),
    path("reports/", include("reports.urls")),
    path("communication/", include("communication.urls")),
    path("about/", about_page, name="about"),
    path("contact/", contact_page, name="contact"),
    path("privacy/", privacy_page, name="privacy"),
    path("terms/", terms_page, name="terms"),
    path("help/", help_page, name="help"),
    path("", landing, name="landing"),
]
