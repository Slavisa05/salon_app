from django.urls import path
from . import views

app_name = 'salon'

urlpatterns = [
    # pages
    path('<str:salon_name>/salons/', views.salon_dashboard, name='salon_dashboard'),
    path('<str:salon_name>/services/', views.services_page, name='services_page'),
    path('<str:salon_name>/schedule/', views.appointments_page, name='appointments'),
    path('<str:salon_name>/slots/', views.get_slots_for_date, name='get_slots'),
    path('create_salon/', views.create_salon, name='create_salon'),
    path('<str:salon_name>/edit_salon/', views.edit_salon, name='edit_salon'),

    # services
    path('<str:salon_name>/services/create', views.create_service, name='create_service'),
    path('<str:salon_name>/services/<int:service_id>/update', views.update_service, name='update_service'),
    path('<str:salon_name>/services/<int:service_id>/delete', views.delete_service, name='delete_service'),

    # appoitments
    path('<str:salon_name>/slots/<int:slot_id>/block/', views.block_slot, name='block_slot'),
    path('<str:salon_name>/slots/<int:slot_id>/unblock/', views.unblock_slot, name='unblock_slot'),
    path('<str:salon_name>/slots/<int:slot_id>/appointment/', views.appointment_details, name='appointment_details'),
    path('<str:salon_name>/slots/<int:slot_id>/appointment/cancel/', views.cancel_appointment, name='cancel_appointment'),
]