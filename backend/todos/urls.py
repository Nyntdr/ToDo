from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    RegisterView,
    UserProfileView,
    TodoListCreateView,
    TodoDetailView,
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', obtain_auth_token, name='login'), # built-in DRF view: takes username & password, returns token
    path('auth/profile/', UserProfileView.as_view(), name='profile'),

    # To-Do CRUD endpoints
    path('todos/', TodoListCreateView.as_view(), name='todo-list-create'),
    path('todos/<int:pk>/', TodoDetailView.as_view(), name='todo-detail'),
]