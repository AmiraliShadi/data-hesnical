from django.urls import path

from . import views

urlpatterns = [
    path('chat-gpt/', views.ChatGPTAPIView.as_view(), name='chat-gpt'),
]
