from django.urls import path
from .views import OrderListCreateView, OrderDetailView, TransactionListCreateView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order_list_create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction_list_create'),
]
