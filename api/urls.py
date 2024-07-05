from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('users_list/', UsersListView.as_view()),
    path('send_interest_request/', SendInterestView.as_view()),
    path('view_interest_requests/', ListInterestRequestView.as_view()),
    path('accept_reject_request/', AcceptOrRejectRequestView.as_view()),
    path('chat_log/', ChatLogView.as_view()),
]
