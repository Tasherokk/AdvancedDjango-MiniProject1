from celery import shared_task
from django.utils import timezone
import csv
import os
from django.conf import settings
from apps.trading.models import Order, Transaction
from apps.sales.models import SalesOrder

@shared_task
def generate_report_task(report_type='csv'):
    """
    A simple Celery task to generate a CSV of recent transactions or sales.
    """
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analytics_report_{timestamp}.{report_type}"

    # Example: gather all Orders
    orders = Order.objects.all().select_related('product', 'user')
    sales_orders = SalesOrder.objects.all().select_related('customer')

    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["OrderID", "User", "Product", "OrderType", "Quantity", "Price", "CreatedAt"])
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.product.name,
                order.order_type,
                order.quantity,
                str(order.price),
                order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        writer.writerow([])
        writer.writerow(["SalesOrderID", "Customer", "Status", "CreatedAt", "Total"])
        for so in sales_orders:
            writer.writerow([
                so.id,
                so.customer.username,
                so.status,
                so.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                str(so.total),
            ])

    # Optionally store in AnalyticsReport model (if you want a record)
    # from .models import AnalyticsReport
    # report_obj = AnalyticsReport.objects.create(
    #     report_name=f"Report {timestamp}",
    # )
    # report_obj.file.name = f'reports/{filename}'
    # report_obj.save()

    return file_path



def generate_report_synchronously():
    """
    Direct function to generate a CSV (synchronously).
    Returns the file path.
    """
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analytics_report_{timestamp}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    orders = Order.objects.select_related('product', 'user').all()
    sales_orders = SalesOrder.objects.select_related('customer').all()

    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["OrderID", "User", "Product", "OrderType", "Quantity", "Price", "CreatedAt"])
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.product.name,
                order.order_type,
                order.quantity,
                str(order.price),
                order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        writer.writerow([])
        writer.writerow(["SalesOrderID", "Customer", "Status", "CreatedAt", "Total"])
        for so in sales_orders:
            writer.writerow([
                so.id,
                so.customer.username,
                so.status,
                so.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                str(so.total),
            ])
    return file_path