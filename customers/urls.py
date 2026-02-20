from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # pages
    path('home/', views.home, name='home'),
    path('moji-termini/', views.my_appointments, name='my_appointments'),
    path('<str:salon_name>/zakazi/', views.booking_form, name='booking_form'),
    path('<str:salon_name>/slobodni-termini/', views.available_slots, name='available_slots'),
]