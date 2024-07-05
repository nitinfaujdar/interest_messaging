import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
import urllib.parse
from django.core.paginator import Paginator

from .models import *

UserModel = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        query_params = urllib.parse.parse_qs(query_string)
        self.username = query_params.get('username', [None])[0]
        self.room_group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.set_online_status(True)
        await self.receive_read_confirmation()
        await self.accept()
        await self.send_initial_messages()
        await self.reset_counter()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.set_online_status(False)

    # For updating the read status of the messages in the database
    async def receive_read_confirmation(self):
        user = await sync_to_async(UserModel.objects.get)(username=self.username)
        await sync_to_async(ChatUserMapping.objects.filter(Q(chat=self.chat_id) & 
                        ~Q(user_name=user.name) & Q(read=False)).update)(read=True)

    # For updating the message counters respectively to 0 for associated user
    async def reset_counter(self):
        user = await sync_to_async(UserModel.objects.get)(username=self.username)
        chat = await sync_to_async(Interest.objects.get)(id=self.chat_id)
        if chat.sender == user.id:
            chat.sender_counter = 0
        else:
            chat.receiver_counter = 0
        await sync_to_async(chat.save)()

    # Online status update in database at real-time
    async def set_online_status(self, status):
        username = self.username
        user = await sync_to_async(UserModel.objects.get)(username=username)
        user.online = status
        if status:
            user.last_activity = timezone.now()
        await sync_to_async(user.save)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "update_online_status",
                "chat_id": self.chat_id,
                "status": status
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json["type"]
        if type == "reaction_update":
            emoji = text_data_json["emoji"]
            id = text_data_json["id"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "reaction_update",
                    "type":type,
                    "emoji": emoji,
                    "id": id,
                }
            )

        elif type == "typing_update":
            user_name = text_data_json["user_name"]
            status = text_data_json["status"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_update",
                    "user_name":user_name,
                    "status": status
                }
            )
        
        elif type == "pagination":
            page = text_data_json["page"]
            await self.send_paginated_messages(page)

        else:
            mess_id = str(uuid.uuid4())
            message = text_data_json["message"]
            username = text_data_json["username"]
            chat = await sync_to_async(Interest.objects.select_related('sender', 'receiver').get)(id=self.chat_id)
            user = await sync_to_async(UserModel.objects.get)(username=username)
            if chat.sender == user:
                chat_user = chat.sender
            else:
                chat_user = chat.receiver
            await self.save_message(username, message, mess_id, chat_user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "id": mess_id,
                    "type": "send_message",
                    "message": message,
                    "username": username,
                    "user_name": chat_user.name,
                    "read": chat_user.online,
                    "created_at": str(timezone.now()),
                    "reaction": None
                }
            )

    # Updating message on the chat screen at real time
    async def send_message(self, event):
        mess_id = event["id"]
        message = event["message"]
        username = event["username"]
        read = event["read"]
        user_name = event["user_name"]
        await self.send(text_data=json.dumps({
                "id": mess_id,
                "message": message,
                "username": username,
                "user_name": user_name,
                "read": read,
                "created_at": str(timezone.now()),
                "reaction": None
            }))
        
    # For updating the reaction of a particular message at real time
    async def reaction_update(self, event):
            id = event["id"]
            emoji = event["emoji"]
            type = event["type"]
            await self.send(text_data=json.dumps({
                    "id": id,
                    "type": type,
                    "reaction": emoji
                }))
    
    # For online status while chatting at real-time
    async def update_online_status(self, event):
        chat_id = event["chat_id"]
        status = event["status"]

        await self.send(text_data=json.dumps({
            "type": "online_status_update",
            "chat_id": chat_id,
            "status": status
        }))
    
    # For updating the typing status while chatting at real-time
    async def typing_update(self, event):
            type = event["type"]
            user_name = event["user_name"]
            status = event["status"]
            await self.send(text_data=json.dumps({
                    "type":type,
                    "status": status,
                    "user_name": user_name,
                }))
    
    # For saving the chats in to the database along with the counters, last_message and user name
    async def save_message(self, username, message, mess_id, chat_user):
        user = await sync_to_async(UserModel.objects.get)(username=username)
        message_obj = await sync_to_async(Interest.objects.select_related('sender', 'receiver').get)(
            id=self.chat_id,
        )
        
        if user == message_obj.student and chat_user.online == False:
           message_obj.mentor_counter += 1
        elif user == message_obj.mentor and chat_user.online == False:
           message_obj.student_counter += 1

        message_obj.last_message = message
        message_obj.last_sent = user.name
        await sync_to_async(message_obj.save)()
        
        _ = await sync_to_async(ChatUserMapping.objects.create)(
            id=mess_id,
            chat=message_obj,
            reaction=None,
            messages=message,
            user_name=user.name,
            read=chat_user.online
        )

    # Pagination for the initial chats page 
    async def send_initial_messages(self):
        chats = await sync_to_async(list)(ChatUserMapping.objects.filter(chat=self.chat_id).order_by('-created_at'))
        paginator = Paginator(chats, per_page=30)
        page_number = 1
        if paginator.count == 0:
            return []
        messages = paginator.get_page(page_number)
        for message in messages:
            await self.send(text_data=json.dumps({
                "type": "pagination",
                "id": str(message.id),
                "message": message.messages,
                "reaction": message.reaction,
                "user_name": message.user_name,
                "read": message.read,
                "created_at": str(message.created_at)
            }))

    # For pagination on chat page after the initial page
    async def send_paginated_messages(self, page):
        chats = await sync_to_async(list)(ChatUserMapping.objects.filter(chat=self.chat_id).order_by('-created_at'))
        paginator = Paginator(chats, per_page=30)
        if page < 1 or page > paginator.num_pages:
            return []
        messages = paginator.get_page(page)
        for message in messages:
            await self.send(text_data=json.dumps({
                "type": "pagination",
                "id": str(message.id),
                "message": message.messages,
                "reaction": message.reaction,
                "user_name": message.user_name,
                "read": message.read,
                "created_at": str(message.created_at)
            }))

        

    
