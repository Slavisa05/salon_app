from django.contrib import admin
from .models import Salon, Service, SalonWorkingHours, TimeSlot, Appointment

admin.site.register(Salon)
admin.site.register(Service)
admin.site.register(SalonWorkingHours)
admin.site.register(TimeSlot)
admin.site.register(Appointment)