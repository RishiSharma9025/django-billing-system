from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("demo-data/", views.generate_demo_data, name="generate_demo_data"),
]

