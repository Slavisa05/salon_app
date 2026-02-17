from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # pages
    path('home/', views.home, name='home'),
]