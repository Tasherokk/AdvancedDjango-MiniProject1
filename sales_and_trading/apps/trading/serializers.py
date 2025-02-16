from rest_framework import serializers
from .models import Order, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'order_type', 'quantity', 'price', 'created_at', 'transactions']
