from django.urls import path
from . import views

urlpatterns = [
    # Salons
    path('salons/', views.salon_dashboard, 'salon_dashboard')
]