from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_list, name="list"),
    path("add/", views.payment_add, name="add"),
    path("invoice/<int:invoice_id>/", views.payment_history, name="history"),
]

