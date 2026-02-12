from django.urls import path
from . import views

app_name = 'salon'

urlpatterns = [
    # pages
    path('<int:salon_id>/salons/', views.salon_dashboard, name='salon_dashboard'),
    path('<int:salon_id>/services/', views.services_page, name='services_page'),
    path('<int:salon_id>/schedule/', views.appointments_page, name='appointments'),
    path('<int:salon_id>/slots/', views.get_slots_for_date, name='get_slots'),

    # appoitments
    path('<int:salon_id>/slots/<int:slot_id>/block/', views.block_slot, name='block_slot'),
    path('<int:salon_id>/slots/<int:slot_id>/unblock/', views.unblock_slot, name='unblock_slot'),
    path('<int:salon_id>/slots/<int:slot_id>/appointment/', views.appointment_details, name='appointment_details'),
    path('<int:salon_id>/slots/<int:slot_id>/appointment/cancel/', views.cancel_appointment, name='cancel_appointment'),
]