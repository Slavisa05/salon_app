import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistem_zakazivanja.settings')

app = Celery('sistem_zakazivanja')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()