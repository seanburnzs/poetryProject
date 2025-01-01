import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Authentication check: ensure user is a participant of the conversation
        is_participant = await self.is_participant(self.conversation_id, self.user)
        if not is_participant:
            logger.warning(f"User {self.user} not a participant in conversation {self.conversation_id}")
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user} connected to conversation {self.conversation_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user} disconnected from conversation {self.conversation_id}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.debug(f"Received data: {data}")

            if data.get('message'):
                # Handle new message
                message_body = data['message']
                # Save message to database
                message = await self.save_message(self.user, self.conversation_id, message_body)
                # Prepare message HTML
                message_html = await self.render_message(message)
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_html': message_html
                    }
                )
                logger.info(f"User {self.user} sent message {message.id}")

        except Exception as e:
            logger.exception(f"Error in receive method: {e}")
            await self.close()

    # Receive message from room group
    async def chat_message(self, event):
        message_html = event['message_html']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message_html': message_html
        }))
        logger.debug("Sent chat message to WebSocket.")

    # Handle unsend message from room group
    async def unsend_message(self, event):
        message_id = event['message_id']
        # Send unsend notification to WebSocket
        await self.send(text_data=json.dumps({
            'unsend': True,
            'message_id': message_id
        }))
        logger.debug(f"Sent unsend notification for message {message_id} to WebSocket.")

    @database_sync_to_async
    def save_message(self, sender, conversation_id, body):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                body=body,
                timestamp=timezone.now()
            )
            conversation.last_updated = timezone.now()
            conversation.save()
            logger.debug(f"Message {message.id} saved to database.")
            return message
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conversation_id} does not exist.")
            raise

    @database_sync_to_async
    def render_message(self, message):
        try:
            return render_to_string('poetry_app/includes/message_item.html', {
                'message': message,
                'user': self.user  # Pass 'user' instead of 'request.user'
            })
        except Exception as e:
            logger.error(f"Error rendering message: {e}")
            raise

    @database_sync_to_async
    def is_participant(self, conversation_id, user):
        is_participant = Conversation.objects.filter(id=conversation_id, participants=user).exists()
        logger.debug(f"User {user} is participant: {is_participant}")
        return is_participant
