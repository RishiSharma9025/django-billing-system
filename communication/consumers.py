import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import ChatMessage, ChatRoom, Notification
from users.models import Business
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_{self.room_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data or "{}")
        msg = (data.get("message") or "").strip()
        if not msg:
            return
        sender_id = self.scope["user"].id if self.scope.get("user") and self.scope["user"].is_authenticated else None
        payload = await self._save_message(self.room_id, sender_id, msg)
        notify_ids = payload.pop("notify_ids", [])
        await self.channel_layer.group_send(self.group_name, {"type": "chat_message", "payload": payload})
        for uid in notify_ids:
            await self.channel_layer.group_send(
                f"notif_{uid}",
                {"type": "notify", "payload": {"type": "count", "count": await self._unread_count(uid)}},
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _save_message(self, room_id, sender_id, message):
        room = ChatRoom.objects.filter(id=room_id).first()
        if room is None:
            biz = Business.objects.first()
            room = ChatRoom.objects.create(business=biz) if biz else None
        if room is None:
            return {"message": message, "sender": "unknown"}
        row = ChatMessage.objects.create(room=room, sender_id=sender_id, message=message)
        # Keep `ChatRoom.updated_at` in sync so staff/admin can auto-select the
        # most recent business conversation.
        ChatRoom.objects.filter(id=room.id).update(updated_at=timezone.now())
        # Notify business owner and all staff users except sender.
        notify_ids = set()
        if row.sender_id and room.business_id:
            owner_id = room.business.owner_id
            if owner_id and owner_id != row.sender_id:
                notify_ids.add(owner_id)
                Notification.objects.create(
                    user_id=owner_id,
                    type=Notification.Type.CHAT,
                    title="Chat reply received",
                    body=f"New message: {row.message[:80]}",
                )
            for sid in User.objects.filter(is_staff=True).exclude(id=row.sender_id).values_list("id", flat=True):
                notify_ids.add(int(sid))
                Notification.objects.create(
                    user_id=sid,
                    type=Notification.Type.CHAT,
                    title="New owner chat message",
                    body=f"{row.sender.username}: {row.message[:80]}",
                )
        return {
            "id": row.id,
            "message": row.message,
            "sender": row.sender.username if row.sender_id else "unknown",
            "created_at": row.created_at.isoformat(),
            "notify_ids": list(notify_ids),
        }

    @database_sync_to_async
    def _unread_count(self, user_id: int):
        return Notification.objects.filter(user_id=user_id, is_read=False).count()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.group_name = f"notif_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        count = await self._unread_count(user.id)
        await self.send(text_data=json.dumps({"type": "count", "count": count}))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _unread_count(self, user_id: int):
        return Notification.objects.filter(user_id=user_id, is_read=False).count()

