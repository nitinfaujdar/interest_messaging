from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *

def get_new_temp_username(name):
    return f"{name}{(str(uuid.uuid4().hex))[:6]}"

class RegisterView(CreateAPIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        if not UserModel.objects.filter(email=email).exists():
            user_model = UserModel.objects.create(
                username=get_new_temp_username(name), email=email, password=password, 
                name=name
            )
            token, _ = Token.objects.get_or_create(user=user_model)
            return Response({"message": "Registration successfull", "token": token.key}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "User with this email already exist"}, status=status.HTTP_201_CREATED)
        