from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.utils import timezone

from users.decorators import approved_business_required
from users.models import Business

from .models import ChatMessage, ChatRoom, Notification

User = get_user_model()


@login_required
@approved_business_required
def chat_room(request):
    biz = Business.objects.filter(owner=request.user).first()
    businesses = None
    if request.user.is_staff:
        businesses = Business.objects.all().order_by("-id")
        selected = request.GET.get("business")
        if selected:
            biz = businesses.filter(id=selected).first() or businesses.first()
        else:
            # Pick the most recently active business conversation by last message.
            latest_room = (
                ChatRoom.objects.annotate(last_msg=Max("messages__created_at"))
                .select_related("business")
                .order_by("-last_msg")
                .first()
            )
            biz = latest_room.business if latest_room else businesses.first()
    room = ChatRoom.objects.filter(business=biz).first() if biz else None
    if biz and room is None:
        room = ChatRoom.objects.create(business=biz)
    messages = room.messages.select_related("sender").order_by("-created_at")[:50] if room else []
    return render(
        request,
        "communication/chat_room.html",
        {
            "room": room,
            "messages": list(reversed(messages)),
            "businesses": businesses,
            "active_business": biz,
        },
    )


@login_required
def notification_feed(request):
    rows = Notification.objects.filter(user=request.user)[:20]
    data = [
        {
            "id": r.id,
            "title": r.title,
            "body": r.body,
            "type": r.type,
            "is_read": r.is_read,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]
    return JsonResponse({"items": data, "unread": Notification.objects.filter(user=request.user, is_read=False).count()})


@login_required
@approved_business_required
@require_POST
def chat_send(request):
    room_id = request.POST.get("room_id")
    message = (request.POST.get("message") or "").strip()
    if not room_id or not message:
        return JsonResponse({"ok": False}, status=400)
    room = ChatRoom.objects.filter(id=room_id).first()
    if room is None:
        return JsonResponse({"ok": False}, status=404)

    # Security: a normal business user may only post into their own room.
    if not request.user.is_staff:
        owner_id = room.business_id and room.business.owner_id
        if not owner_id or owner_id != request.user.id:
            return JsonResponse({"ok": False}, status=403)

    row = ChatMessage.objects.create(room=room, sender=request.user, message=message)
    # Keep `ChatRoom.updated_at` in sync with the newest message.
    ChatRoom.objects.filter(id=room.id).update(updated_at=timezone.now())

    # Notify business owner and all staff except sender.
    recipient_ids = set()
    owner_id = room.business_id and room.business.owner_id
    if owner_id and owner_id != request.user.id:
        recipient_ids.add(owner_id)
    for sid in User.objects.filter(is_staff=True).exclude(id=request.user.id).values_list("id", flat=True):
        recipient_ids.add(sid)
    for uid in recipient_ids:
        Notification.objects.create(
            user_id=uid,
            type=Notification.Type.CHAT,
            title="Chat reply received",
            body=f"New message: {row.message[:80]}",
        )

    return JsonResponse(
        {
            "ok": True,
            "id": row.id,
            "sender": row.sender.username,
            "message": row.message,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M"),
        }
    )


@login_required
@approved_business_required
def chat_messages(request):
    room_id = request.GET.get("room_id")
    since_id = int(request.GET.get("since_id") or 0)
    room = ChatRoom.objects.filter(id=room_id).first() if room_id else None
    if room is None:
        return JsonResponse({"items": [], "last_id": since_id})

    # Security: a normal business user may only read their own room messages.
    if not request.user.is_staff:
        owner_id = room.business_id and room.business.owner_id
        if not owner_id or owner_id != request.user.id:
            return JsonResponse({"items": [], "last_id": since_id})

    rows = room.messages.select_related("sender").filter(id__gt=since_id).order_by("id")[:100]
    items = [
        {
            "id": r.id,
            "sender": r.sender.username,
            "message": r.message,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]
    last_id = rows.aggregate(mx=Max("id")).get("mx") or since_id
    return JsonResponse({"items": items, "last_id": last_id})

