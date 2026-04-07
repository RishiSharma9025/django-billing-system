from django.conf import settings
from django.db import models

from users.models import Business


class ChatRoom(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="chat_room")
    updated_at = models.DateTimeField(auto_now=True)


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class Notification(models.Model):
    class Type(models.TextChoices):
        CHAT = "chat", "Chat Reply"
        PAYMENT_DUE = "payment_due", "Payment Due"
        INVOICE_OVERDUE = "invoice_overdue", "Invoice Overdue"
        SYSTEM = "system", "System Alert"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

