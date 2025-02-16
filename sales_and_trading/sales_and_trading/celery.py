import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_and_trading.settings')

app = Celery('sales_and_trading')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
