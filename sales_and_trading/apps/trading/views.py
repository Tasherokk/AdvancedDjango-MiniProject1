from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Order, Transaction
from .serializers import OrderSerializer, TransactionSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        executed_price = serializer.validated_data['executed_price']
        quantity = serializer.validated_data['quantity']
        serializer.save(executed_at=timezone.now())
