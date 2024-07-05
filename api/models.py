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
    image = models.CharField(max_length=250, null=True, blank=True)
    online = models.BooleanField(default=False)

class Interest(Common, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, related_name="receiver")
    sender_counter = models.IntegerField(default=0, null=False, blank=False)
    receiver_counter = models.IntegerField(default=0, null=False, blank=False)
    last_message = models.CharField(max_length=555, null=True, blank=False)
    last_sent = models.CharField(max_length=20, null=True, blank=False)
    status = models.CharField(max_length=10, choices=[('sent', 'Sent'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])

class ChatUserMapping(Common, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey('Interest', on_delete=models.CASCADE)
    reaction = models.CharField(max_length=500, null=True, blank=True)
    user_name = models.CharField(max_length=20, null=True, blank=True)
    read = models.BooleanField(default=False)
    messages = models.TextField(null=True, blank=True)