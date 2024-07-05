from django.shortcuts import render
from rest_framework.generics import GenericAPIView, CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .serializers import *

def get_new_temp_username(name):
    return f"{name}{(str(uuid.uuid4().hex))[:6]}"

# Registeration API
class RegisterView(CreateAPIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        if not email or not password or not name:
            return Response({"Error": "Email, Password and Name are required."}, status=status.HTTP_400_BAD_REQUEST)
        if not UserModel.objects.filter(email=email).exists():
            user_model = UserModel.objects.create(
                username=get_new_temp_username(name), email=email, password=password, 
                name=name
            )
            return Response({"message": "Registration successfull"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"Error": "User with this email already exist"}, status=status.HTTP_400_BAD_REQUEST)

# Login API
class LoginView(CreateAPIView):
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({"Error": "Email and Password are required."}, status=status.HTTP_400_BAD_REQUEST)
        user = UserModel.objects.get(email=email)
        if user.check_password(password):
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"message": "Login successfull", "token": token.key}, status=status.HTTP_201_CREATED)
        else:
            return Response({"Error": "User with this email already exist"}, status=status.HTTP_400_BAD_REQUEST)

# List of users in the application
class UsersListView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def get(self, request):
        obj = UserModel.objects.all()
        page = self.paginate_queryset(obj)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response({"message": "List of Users", "data": response.data}, status=status.HTTP_200_OK)

# For sending the interest request to the user
class SendInterestView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InterestSerializer

    def post(self, request):
        sender_id = request.user.id
        receiver_id = request.data.get('receiver')
        if not sender_id or not receiver_id:
            return Response({"Error": "Sender and Receiver are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the combination of sender and receiver already exists with 'sent' or 'accepted' status
        existing_interest = Interest.objects.filter(
            Q(sender=sender_id, receiver=receiver_id) &
            Q(sender=receiver_id, receiver=sender_id) &
            Q(status__in=['sent', 'accepted'])
        ).exists()

        if existing_interest:
            return Response({"error": "Interest request already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the interest request
        interest_data = {
            'sender': sender_id,
            'receiver': receiver_id,
            'status': 'sent'
        }
        serializer = self.get_serializer(data=interest_data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Interest request sent successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# For list of interest requests
class ListInterestRequestView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InterestSerializer
    pagination_class = PageNumberPagination

    def get(self, request):
        obj = Interest.objects.filter(receiver=request.user.id, status='sent')
        page = self.paginate_queryset(obj)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response({"message": "List of Interest Request", "data": response.data}, status=status.HTTP_200_OK)

# For accepting or rejecting the interest request
class AcceptOrRejectRequestView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = request.data.get('id')
        status = request.data.get('status')
        if not request_id or not status:
            return Response({"Error": "Request ID and status are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = Interest.objects.get(id=request_id)
        except Interest.DoesNotExist:
            raise serializers.ValidationError({
                "Error": "Invalid Request ID supplied"
            })
        if status == 'accepted':
            obj.status = status
            obj.save()
            return Response({"message": "Request accepted successfully"}, status=status.HTTP_200_OK)
        else:
            obj.delete()
            return Response({"message": "Request rejected Successfully"}, status=status.HTTP_200_OK)

# For the list of users chat is enabled for
class ChatLogView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InterestSerializer
    pagination_class = PageNumberPagination

    def get(self, request):
        obj = Interest.objects.filter(Q(sender=request.user, status='accepted') | Q(receiver=request.user, status='accepted') )
        page = self.paginate_queryset(obj)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response({"message": "Chat Log retrieved successfully", "data": response.data}, status=status.HTTP_200_OK)