from django.urls import path

from .views import login_view, logout_view, register_business

urlpatterns = [
    path("login/", login_view, name="user_login"),
    path("logout/", logout_view, name="user_logout"),
    path("register/", register_business, name="register_business"),
]

