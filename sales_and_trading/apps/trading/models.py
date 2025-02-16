# apps/trading/models.py

from django.db import models
from django.conf import settings
from apps.products.models import Product

class Order(models.Model):
    ORDER_TYPE_CHOICES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optionally track if the order is still active, partially filled, closed, etc.
    status = models.CharField(max_length=20, default='active')
    # 'active', 'closed', 'cancelled', etc.

    def __str__(self):
        return f"{self.order_type.upper()} #{self.id} - {self.product.name} x {self.quantity}"

class Transaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    executed_at = models.DateTimeField(auto_now_add=True)
    executed_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Transaction #{self.id} for Order #{self.order.id}"
