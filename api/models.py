from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

class Common(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(Common, AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(max_length=20)
    name = models.CharField(max_length=150)

class Message(Common, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name="m_sender")
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, related_name="m_receiver")
    status = models.CharField(max_length=10, choices=[('sent', 'Sent'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])
    is_deleted = models.BooleanField(default=False)

class ChatUserMapping(Common, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey('Message', on_delete=models.CASCADE, related_name="chat_id")
    chat_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="chat_user")
    reaction = models.CharField(max_length=500, null=True, blank=True)
    read = models.BooleanField(default=False)
    messages = models.TextField()