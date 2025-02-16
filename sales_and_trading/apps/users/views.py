from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class UserListCreateView(generics.ListCreateAPIView):
    """
    Allows Admin to list users, and also handle user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            # Only Admin can view user list
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Allows user detail retrieve/update by Admin or the user themself.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsOwnerOrAdmin()]  # custom permission we define below
        return super().get_permissions()

from rest_framework.permissions import BasePermission

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to allow only the user or an admin to edit user data.
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff
