from django.urls import path

from . import views

app_name = "invoices"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("create/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
]

