from django.urls import path

from . import views

app_name = "communication"

urlpatterns = [
    path("chat/", views.chat_room, name="chat_room"),
    path("notifications/", views.notification_feed, name="notification_feed"),
    path("chat/send/", views.chat_send, name="chat_send"),
    path("chat/messages/", views.chat_messages, name="chat_messages"),
]

