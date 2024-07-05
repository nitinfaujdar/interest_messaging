from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

UserModel = get_user_model()

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ['id', 'name', 'email', 'image']

class InterestSerializer(serializers.ModelSerializer):
    sender_details = serializers.SerializerMethodField('get_sender_details')
    receiver_details = serializers.SerializerMethodField('get_receiver_details')

    class Meta:
        model = Interest
        fields = ['id', 'sender', 'sender_details', 'receiver', 'receiver_details', 'status', 'sender_counter', 'receiver_counter', 
            'last_message', 'last_sent']

    @classmethod    
    def get_sender_details(self, obj):
        return UserModel.objects.filter(id=obj.sender).values('id', 'name', 'image')
    
    @classmethod
    def get_receiver_details(self, obj):
        return UserModel.objects.filter(id=obj.receiver).values('id', 'name', 'image')