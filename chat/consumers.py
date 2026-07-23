import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We add everyone to the "agents_group"
        self.group_name = 'agents_group'

        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    # Receive message from room group
    async def chat_update(self, event):
        # The event will contain whatever data we send from the webhook
        # For example, we might just send {"type": "chat_update", "action": "refresh"}
        # Or we can send specific payload
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))
