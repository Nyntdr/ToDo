from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import Todo
from .serializers import TodoSerializer, RegisterSerializer, UserSerializer


# -----------------------------------------------------------------------------
# AUTH VIEWS
# -----------------------------------------------------------------------------

class RegisterView(generics.CreateAPIView):
    """
    POST: Register a new user and immediately return an auth token.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can sign up

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Automatically generate a Token for this user upon registration
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key
        })


class UserProfileView(generics.RetrieveAPIView):
    """
    GET: Retrieve the currently logged-in user's profile info.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# -----------------------------------------------------------------------------
# TO-DO CRUD VIEWS (Generic Class-Based Views)
# -----------------------------------------------------------------------------

class TodoListCreateView(generics.ListCreateAPIView):
    """
    GET: List todos belonging to the authenticated user.
    POST: Create a new todo assigned to the authenticated user.
    """
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Authorization: Only return todos owned by the requesting user
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Auto-assign the logged in user as the owner
        serializer.save(user=self.request.user)


class TodoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /<id>/: Retrieve a single todo.
    PUT /<id>/: Full update.
    PATCH /<id>/: Partial update (e.g. toggle completed).
    DELETE /<id>/: Delete a todo.
    """
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Authorization: Users can only retrieve/update/delete their own todos
        return Todo.objects.filter(user=self.request.user)