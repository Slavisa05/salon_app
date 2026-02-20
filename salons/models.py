from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime, timedelta
import math
import logging

logger = logging.getLogger(__name__)


class Salon(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(unique=True)
    image = models.ImageField(default='img/barber_default.jpg')
    address = models.CharField(max_length=200, unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    slot_interval_minutes = models.PositiveSmallIntegerField(
        choices=[(15, '15 minuta'), (30, '30 minuta'), (60, '60 minuta')],
        default=30
    )
    # ovde mozda dodati i komentare i ocene

    class Meta:
        verbose_name_plural = "Saloni"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_approved = False
        if self.pk:
            previous = Salon.objects.filter(pk=self.pk).only('is_approved').first()
            was_approved = previous.is_approved if previous else False

        super().save(*args, **kwargs)

        if is_new and not self.is_approved:
            self._send_pending_approval_email_to_admin()

        if not was_approved and self.is_approved:
            self._send_approval_email()

    def _get_admin_notification_recipients(self):
        recipients = getattr(settings, 'SALON_APPROVAL_NOTIFY_EMAILS', []) or []

        if isinstance(recipients, str):
            recipients = [item.strip() for item in recipients.split(',') if item.strip()]

        if recipients:
            return recipients

        fallback = getattr(settings, 'SALON_APPROVAL_NOTIFY_EMAIL', '')
        return [fallback] if fallback else []

    def _send_pending_approval_email_to_admin(self):
        recipients = self._get_admin_notification_recipients()
        if not recipients:
            return

        try:
            subject_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', '')
            subject = f"{subject_prefix}Novi salon čeka odobrenje"
            owner_email = self.owner.email if self.owner.email else '-'

            message_text = (
                "Kreiran je novi salon koji čeka odobrenje.\n\n"
                f"Salon: {self.name}\n"
                f"Vlasnik: {self.owner.username}\n"
                f"Email vlasnika: {owner_email}\n"
            )
            message_html = f"""
            <html>
              <body style=\"font-family: Arial, sans-serif; color: #1F2937;\">
                <h2>Novi salon čeka odobrenje</h2>
                <p><strong>Salon:</strong> {self.name}</p>
                <p><strong>Vlasnik:</strong> {self.owner.username}</p>
                <p><strong>Email vlasnika:</strong> {owner_email}</p>
              </body>
            </html>
            """

            email_message = EmailMultiAlternatives(
                subject,
                message_text,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
            )
            email_message.attach_alternative(message_html, 'text/html')
            email_message.send(fail_silently=False)
        except Exception:
            logger.exception('Neuspešno slanje emaila adminu za salon koji čeka odobrenje (salon_id=%s).', self.pk)

    def _send_approval_email(self):
        owner_email = self.owner.email
        if not owner_email:
            return

        try:
            subject_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', '')
            subject = f"{subject_prefix}Vaš salon je odobren"
            login_path = getattr(settings, 'LOGIN_URL', '/login/')
            app_base_url = getattr(settings, 'APP_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
            login_url = f"{app_base_url}{login_path}"

            message_text = (
                f"Zdravo, {self.owner.username}!\n\n"
                f"Vaš salon \"{self.name}\" je odobren.\n"
                "Sada možete da se ulogujete i upravljate salonom.\n"
                f"Prijava: {login_url}\n"
            )
            message_html = f"""
            <html>
              <body style=\"font-family: Arial, sans-serif; color: #1F2937;\">
                <h2>Vaš salon je odobren</h2>
                <p>Zdravo, <strong>{self.owner.username}</strong>!</p>
                <p>Vaš salon <strong>{self.name}</strong> je odobren.</p>
                <p>Sada možete da se ulogujete i upravljate salonom.</p>
                <p style=\"margin: 20px 0;\">
                  <a href=\"{login_url}\" style=\"background:#6366F1;color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;display:inline-block;\">Ulogujte se</a>
                </p>
              </body>
            </html>
            """

            email_message = EmailMultiAlternatives(
                subject,
                message_text,
                settings.DEFAULT_FROM_EMAIL,
                [owner_email],
            )
            email_message.attach_alternative(message_html, 'text/html')
            email_message.send(fail_silently=False)
        except Exception:
            logger.exception('Neuspešno slanje emaila vlasniku za odobren salon (salon_id=%s).', self.pk)
    
    def __str__(self):
        return self.name
    

class Service(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.IntegerField(help_text='Trajanje u minutima')

    class Meta:
        unique_together = ['salon', 'name'] 
        verbose_name_plural = "Usluge"
    
    def __str__(self):
        return f"{self.salon.name} - {self.name} ({self.duration}min)"


class SalonWorkingHours(models.Model):
    DAYS = [
        ('ponedeljak', 'Ponedeljak'),
        ('utorak', 'Utorak'),
        ('sreda', 'Sreda'),
        ('cetvrtak', 'Četvrtak'),
        ('petak', 'Petak'),
        ('subota', 'Subota'),
        ('nedelja', 'Nedelja'),
    ]

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='working_hours')
    day = models.CharField(max_length=10 ,choices=DAYS)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_working = models.BooleanField(default=True)

    class Meta:
        unique_together = ['salon', 'day']
        verbose_name_plural = "Salon Working Hours"
        ordering = ['salon', 'day'] 
    
    def clean(self):
        if self.is_working and self.opening_time and self.closing_time:
            if self.opening_time >= self.closing_time:
                raise ValidationError("Vreme otvaranja mora biti pre zatvaranja")
    
    def __str__(self):
        if self.is_working:
            return f"{self.salon.name} - {self.get_day_display()}: {self.opening_time} - {self.closing_time}"
        return f"{self.salon.name} - {self.get_day_display()}: Zatvoreno"


class TimeSlot(models.Model):
    STATUS_CHOICES = [
        ('dostupan', 'Dostupan'), 
        ('zauzet', 'Zauzet'), 
        ('blokiran', 'Blokiran'),
    ]

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='time_slot')
    date = models.DateField(db_index=True)
    begin_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='dostupan')

    class Meta:
        unique_together = ['salon', 'date', 'begin_time']  
        ordering = ['date', 'begin_time']
        verbose_name_plural = "Time Slots"
        indexes = [
            models.Index(fields=['salon', 'date', 'status']),  
        ]
    
    def clean(self):
        if self.begin_time >= self.end_time:
            raise ValidationError("Početno vreme mora biti pre završnog")
    
    def __str__(self):
        return f"{self.salon.name} - {self.date} {self.begin_time}-{self.end_time} ({self.status})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('na čekanju', 'Na čekanju'),
        ('potvrđeno', 'Potvrđeno'),
        ('završeno', 'Završeno'),
        ('otkazano', 'Otkazano'),
        ('nije se pojavio', 'Nije se pojavio'),
    ]

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='appointments')
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE, related_name='appointment') 
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='appointments')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='na čekanju')
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Rezervacije"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            previous = None
            if self.pk:
                previous = Appointment.objects.select_related('time_slot', 'service').get(pk=self.pk)

            if previous and previous.status != 'otkazano':
                if (
                    self.status == 'otkazano'
                    or previous.time_slot_id != self.time_slot_id
                    or previous.service_id != self.service_id
                ):
                    previous_slots = self._get_slots_for(previous.time_slot, previous.service, create_missing=False)
                    self._release_slots(previous_slots, exclude_appointment_id=self.pk)

            if self.status != 'otkazano':
                slots = self._get_slots_for(self.time_slot, self.service, create_missing=True)
                self._assert_slots_available(slots)
                self._mark_slots_busy(slots)

            super().save(*args, **kwargs)

            if self.status == 'otkazano':
                slots = self._get_slots_for(self.time_slot, self.service, create_missing=False)
                self._release_slots(slots, exclude_appointment_id=self.pk)

    def _get_slot_minutes(self, time_slot):
        start = datetime.combine(time_slot.date, time_slot.begin_time)
        end = datetime.combine(time_slot.date, time_slot.end_time)
        minutes = int((end - start).total_seconds() / 60)
        return minutes if minutes > 0 else 30

    def _get_time_range(self, time_slot, service):
        slot_minutes = self._get_slot_minutes(time_slot)
        duration = service.duration if service else slot_minutes
        start = datetime.combine(time_slot.date, time_slot.begin_time)
        end = start + timedelta(minutes=duration)
        required_slots = math.ceil(duration / slot_minutes)
        return start, end, slot_minutes, required_slots

    def _get_slots_for(self, time_slot, service, create_missing=False):
        start, _, slot_minutes, required_slots = self._get_time_range(time_slot, service)
        slots = []

        for index in range(required_slots):
            slot_start = start + timedelta(minutes=slot_minutes * index)
            slot_end = slot_start + timedelta(minutes=slot_minutes)
            slot_start_time = slot_start.time()

            if create_missing:
                slot, _ = TimeSlot.objects.get_or_create(
                    salon=time_slot.salon,
                    date=time_slot.date,
                    begin_time=slot_start_time,
                    defaults={
                        'end_time': slot_end.time(),
                        'status': 'dostupan'
                    }
                )
            else:
                slot = TimeSlot.objects.filter(
                    salon=time_slot.salon,
                    date=time_slot.date,
                    begin_time=slot_start_time
                ).first()

            if slot:
                slots.append(slot)

        if len(slots) < required_slots:
            raise ValidationError('Nema dovoljno slobodnih slotova za izabranu uslugu.')

        return slots

    def _assert_slots_available(self, slots):
        for slot in slots:
            if slot.status == 'blokiran':
                raise ValidationError('Izabrani termin je blokiran.')

            if hasattr(slot, 'appointment') and slot.appointment_id != self.pk:
                raise ValidationError('Izabrani termin je već zauzet.')

            if slot.status == 'zauzet' and not hasattr(slot, 'appointment'):
                raise ValidationError('Izabrani termin je već zauzet.')

    def _mark_slots_busy(self, slots):
        for slot in slots:
            if slot.status != 'zauzet':
                slot.status = 'zauzet'
                slot.save(update_fields=['status'])

    def _release_slots(self, slots, exclude_appointment_id=None):
        if not slots:
            return

        appointments = Appointment.objects.select_related('time_slot', 'service').filter(
            time_slot__salon=slots[0].salon,
            time_slot__date=slots[0].date
        ).exclude(status='otkazano')

        if exclude_appointment_id:
            appointments = appointments.exclude(pk=exclude_appointment_id)

        busy_ranges = []
        for appointment in appointments:
            start, end, _, _ = self._get_time_range(appointment.time_slot, appointment.service)
            busy_ranges.append((start, end))

        for slot in slots:
            if slot.status == 'blokiran':
                continue

            slot_start = datetime.combine(slot.date, slot.begin_time)
            slot_end = datetime.combine(slot.date, slot.end_time)

            overlapping = any(
                slot_start < busy_end and slot_end > busy_start
                for busy_start, busy_end in busy_ranges
            )

            if not overlapping:
                slot.status = 'dostupan'
                slot.save(update_fields=['status'])
    
    def __str__(self):
        return f"{self.customer.username} - {self.time_slot.date} {self.time_slot.begin_time}"


