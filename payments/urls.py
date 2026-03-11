from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("invoice/<int:invoice_id>/", views.record_payment, name="record_payment"),
]

