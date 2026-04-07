from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
try:
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
except Exception:  # pragma: no cover - optional realtime dependency
    async_to_sync = None
    get_channel_layer = None

from invoices.models import Invoice
from payments.models import Payment
from users.models import Business

from .models import Notification

User = get_user_model()


def _owners_for_business(business: Business):
    return User.objects.filter(id=business.owner_id)


def _push_notification_count(user_id: int):
    try:
        if async_to_sync is None or get_channel_layer is None:
            return
        layer = get_channel_layer()
        if layer is None:
            return
        count = Notification.objects.filter(user_id=user_id, is_read=False).count()
        async_to_sync(layer.group_send)(
            f"notif_{user_id}",
            {"type": "notify", "payload": {"type": "count", "count": count}},
        )
    except Exception:
        return


@receiver(post_save, sender=Payment)
def payment_due_notification(sender, instance: Payment, created: bool, **kwargs):
    if not created:
        return
    business = instance.invoice.business
    for user in _owners_for_business(business):
        Notification.objects.create(
            user=user,
            type=Notification.Type.PAYMENT_DUE,
            title="Payment received update",
            body=f"Payment recorded for invoice {instance.invoice.invoice_number}.",
        )
        _push_notification_count(user.id)


@receiver(post_save, sender=Invoice)
def invoice_status_notification(sender, instance: Invoice, created: bool, **kwargs):
    if not created and instance.status in {"unpaid", "partial"}:
        business = instance.business
        for user in _owners_for_business(business):
            Notification.objects.create(
                user=user,
                type=Notification.Type.INVOICE_OVERDUE,
                title="Invoice due alert",
                body=f"Invoice {instance.invoice_number} is currently {instance.get_status_display()}.",
            )
            _push_notification_count(user.id)

