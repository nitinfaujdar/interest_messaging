from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

UserModel = get_user_model()

class InterestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatUserMapping
        fields = '__all__'