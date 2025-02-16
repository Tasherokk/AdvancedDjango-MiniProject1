from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import SalesOrder, SalesOrderItem, Invoice
from .serializers import SalesOrderSerializer, InvoiceSerializer
from sales_and_trading.utils.pdf_utils import render_pdf, pdf_response

from django.contrib.auth import get_user_model
User = get_user_model()

class SalesOrderListCreateView(generics.ListCreateAPIView):
    """
    GET: List all Sales Orders (Admins & Sales can see all, customers see only theirs).
    POST: Create a new Sales Order (Customers can create for themselves).
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'sales']:
            return SalesOrder.objects.all()
        # Customers: only view their own orders
        return SalesOrder.objects.filter(customer=user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['customer'] = request.user.id  # enforce that the customer is the logged-in user
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SalesOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a Sales Order.
    PUT/PATCH: Update the order (e.g., admin/sales can approve).
    DELETE: Cancel or delete the order (admin/sales).
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'sales']:
            return SalesOrder.objects.all()
        return SalesOrder.objects.filter(customer=user)

    def update(self, request, *args, **kwargs):
        """
        If the user is an admin or has 'sales' role, they can change status.
        If the user is a customer, they can only update (maybe) if it's still pending.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        # Convert request data to mutable
        data = request.data.copy()

        # If user is not admin or sales, disallow changing status to approved/completed
        if user.role not in ['admin', 'sales'] and 'status' in data:
            if data['status'] in ['approved', 'completed']:
                return Response({"detail": "Not allowed to approve/complete orders."},
                                status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

class InvoiceCreateView(generics.CreateAPIView):
    """
    Create an invoice for a given SalesOrder.
    Only Admin or Sales can generate an invoice once order is approved.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        order_id = self.request.data.get('sales_order')
        sales_order = get_object_or_404(SalesOrder, id=order_id)

        # Only Admin or Sales can create invoices
        if user.role not in ['admin', 'sales']:
            raise permissions.PermissionDenied("You do not have permission to create invoices.")

        # Only allow invoice creation if order is approved
        if sales_order.status != 'approved':
            raise ValueError("Cannot generate invoice for non-approved order.")

        # Ensure invoice doesn’t already exist
        if hasattr(sales_order, 'invoice'):
            raise ValueError("Invoice already exists for this order.")

        serializer.save(sales_order=sales_order)

class InvoiceRetrievePDFView(generics.RetrieveAPIView):
    """
    Retrieve an existing invoice and return as a PDF download.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        invoice = self.get_object()
        sales_order = invoice.sales_order
        context = {
            'invoice': invoice,
            'sales_order': sales_order,
            'items': sales_order.items.all(),
            'customer': sales_order.customer,
            'total': sales_order.total,
            'date': timezone.now(),
        }
        # We assume we have a templates/invoice_template.html
        pdf_content = render_pdf('invoice_template.html', context_dict=context)
        return pdf_response(pdf_content, filename=f"invoice_{invoice.id}.pdf")
