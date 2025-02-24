from celery import shared_task
from django.utils import timezone
import csv
import os
from django.conf import settings
from apps.trading.models import Order
from apps.sales.models import SalesOrder


@shared_task
def generate_report_task(report_type='csv'):
    """
    Целевой таск Celery для генерации CSV (или другого формата)
    по ордерам и продажам с дополнительной сводной аналитикой.
    """
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analytics_report_{timestamp}.{report_type}"

    # Получаем нужные данные
    orders = Order.objects.select_related('product', 'user').all()
    sales_orders = SalesOrder.objects.select_related('customer').all()

    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        # Используем точку с запятой, чтобы Excel корректно делил поля
        # в регионах, где запятая – десятичный разделитель.
        writer = csv.writer(
            csvfile,
            delimiter=';',  # <-- ключевая часть
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )

        # --- Блок 1: Сырые данные по Orders ---
        writer.writerow(["OrderID", "User", "Product", "OrderType", "Quantity", "Price", "CreatedAt"])
        for order in orders:
            writer.writerow([
                order.id,
                order.user.username,
                order.product.name,
                order.order_type,
                order.quantity,
                str(order.price),  # или можно f"{order.price:.2f}"
                order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        # --- Блок 2: Сырые данные по Sales Orders ---
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

        # --- Блок 3: Дополнительная аналитика (суммы/средние и т.д.) ---
        # Простейший пример агрегации
        total_orders = orders.count()
        total_quantity = sum(o.quantity for o in orders)
        total_amount = sum(o.quantity * o.price for o in orders)

        total_sales_orders = sales_orders.count()
        total_sales_sum = sum(so.total for so in sales_orders)

        # Добавляем заголовок для раздела аналитики
        writer.writerow([])
        writer.writerow(["=== ANALYTICS ==="])
        writer.writerow(["Total Orders", total_orders])
        writer.writerow(["Total Quantity (all Orders)", total_quantity])
        writer.writerow(["Total Amount (all Orders)", f"{total_amount:.2f}"])

        writer.writerow([])
        writer.writerow(["Total Sales Orders", total_sales_orders])
        writer.writerow(["Total Sales Sum", f"{total_sales_sum:.2f}"])

    return file_path


def generate_report_synchronously():
    """
    Прямой (синхронный) вариант функции для генерации CSV.
    Аналогично выше, но без Celery.
    """
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analytics_report_{timestamp}.csv"
    file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    orders = Order.objects.select_related('product', 'user').all()
    sales_orders = SalesOrder.objects.select_related('customer').all()

    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(
            csvfile,
            delimiter=';',  # аналогично, чтобы Excel корректно "читал" CSV
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )

        # --- Сырые данные по Orders ---
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

        # --- Сырые данные по Sales Orders ---
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

        # --- Пример аналитики ---
        total_orders = orders.count()
        total_quantity = sum(o.quantity for o in orders)
        total_amount = sum(o.quantity * o.price for o in orders)

        total_sales_orders = sales_orders.count()
        total_sales_sum = sum(so.total for so in sales_orders)

        writer.writerow([])
        writer.writerow(["=== ANALYTICS ==="])
        writer.writerow(["Total Orders", total_orders])
        writer.writerow(["Total Quantity (all Orders)", total_quantity])
        writer.writerow(["Total Amount (all Orders)", f"{total_amount:.2f}"])
        writer.writerow([])
        writer.writerow(["Total Sales Orders", total_sales_orders])
        writer.writerow(["Total Sales Sum", f"{total_sales_sum:.2f}"])

    return file_path


# from celery import shared_task
# from django.utils import timezone
# import csv
# import os
# from django.conf import settings
# from apps.trading.models import Order, Transaction
# from apps.sales.models import SalesOrder
#
# @shared_task
# def generate_report_task(report_type='csv'):
#     """
#     A simple Celery task to generate a CSV of recent transactions or sales.
#     """
#     timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"analytics_report_{timestamp}.{report_type}"
#
#     # Example: gather all Orders
#     orders = Order.objects.all().select_related('product', 'user')
#     sales_orders = SalesOrder.objects.all().select_related('customer')
#
#     file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#
#     with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(["OrderID", "User", "Product", "OrderType", "Quantity", "Price", "CreatedAt"])
#         for order in orders:
#             writer.writerow([
#                 order.id,
#                 order.user.username,
#                 order.product.name,
#                 order.order_type,
#                 order.quantity,
#                 str(order.price),
#                 order.created_at.strftime("%Y-%m-%d %H:%M:%S")
#             ])
#
#         writer.writerow([])
#         writer.writerow(["SalesOrderID", "Customer", "Status", "CreatedAt", "Total"])
#         for so in sales_orders:
#             writer.writerow([
#                 so.id,
#                 so.customer.username,
#                 so.status,
#                 so.created_at.strftime("%Y-%m-%d %H:%M:%S"),
#                 str(so.total),
#             ])
#
#     # Optionally store in AnalyticsReport model (if you want a record)
#     # from .models import AnalyticsReport
#     # report_obj = AnalyticsReport.objects.create(
#     #     report_name=f"Report {timestamp}",
#     # )
#     # report_obj.file.name = f'reports/{filename}'
#     # report_obj.save()
#
#     return file_path
#
#
#
# def generate_report_synchronously():
#     """
#     Direct function to generate a CSV (synchronously).
#     Returns the file path.
#     """
#     timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"analytics_report_{timestamp}.csv"
#     file_path = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#
#     orders = Order.objects.select_related('product', 'user').all()
#     sales_orders = SalesOrder.objects.select_related('customer').all()
#
#     with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(["OrderID", "User", "Product", "OrderType", "Quantity", "Price", "CreatedAt"])
#         for order in orders:
#             writer.writerow([
#                 order.id,
#                 order.user.username,
#                 order.product.name,
#                 order.order_type,
#                 order.quantity,
#                 str(order.price),
#                 order.created_at.strftime("%Y-%m-%d %H:%M:%S")
#             ])
#
#         writer.writerow([])
#         writer.writerow(["SalesOrderID", "Customer", "Status", "CreatedAt", "Total"])
#         for so in sales_orders:
#             writer.writerow([
#                 so.id,
#                 so.customer.username,
#                 so.status,
#                 so.created_at.strftime("%Y-%m-%d %H:%M:%S"),
#                 str(so.total),
#             ])
#     return file_path