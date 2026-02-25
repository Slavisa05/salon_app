from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from salons.models import Appointment

@shared_task
def update_appointment_statuses():
    print("CELERY TASK POKRENUT")
    now = timezone.now()
    appointments = Appointment.objects.select_related('time_slot', 'service').exclude(status__in=['otkazano', 'završeno', 'nije se pojavio'])
    print(f"Pronađeno termina za azuriranje: {appointments.count()}")
    for appt in appointments:
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(appt.time_slot.date, appt.time_slot.begin_time),
            timezone.get_current_timezone()
        )
        duration = appt.service.duration if appt.service else 30
        end_datetime = start_datetime + timedelta(minutes=duration)
        print(f"Termin: {appt}, Status: {appt.status}, Vreme: {start_datetime} - {end_datetime}, NOW: {now}")
        
        # UVEK prvo proveri da li je termin završen
        if now >= end_datetime and appt.status != 'završeno':
            appt.status = 'završeno'
            appt.save(update_fields=['status'])
            print(f"Status promenjen u 'završeno': {appt.id}")
        # Onda proveri da li je u toku
        elif now >= start_datetime and now < end_datetime and appt.status == 'na čekanju':
            appt.status = 'u toku'
            appt.save(update_fields=['status'])
            print(f"Status promenjen u 'u toku': {appt.id}")