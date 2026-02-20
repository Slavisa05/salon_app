from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from salons.models import Salon, Service, TimeSlot, Appointment
from salons.utils import generate_time_slots_for_date
from sistem_zakazivanja.models import UserProfile

def home(request):
    salons = Salon.objects.filter(is_approved=True, is_active=True)

    return render(request, 'customers/home.html', {'salons': salons})


def _is_customer(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile.role == 'musterija'


@login_required
def booking_form(request, salon_name):
    if not _is_customer(request.user):
        messages.error(request, 'Samo musterije mogu zakazivati termine.')
        return redirect('redirect_after_login')

    salon = get_object_or_404(Salon, name=salon_name, is_approved=True, is_active=True)
    services = salon.services.all().order_by('name')

    if request.method == 'POST':
        service_id = request.POST.get('service')
        slot_id = request.POST.get('slot')
        notes = request.POST.get('notes', '').strip()

        if not service_id or not slot_id:
            messages.error(request, 'Izaberite uslugu i termin.')
            return redirect('customers:booking_form', salon_name=salon.name)

        service = get_object_or_404(Service, id=service_id, salon=salon)
        slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

        if slot.status != 'dostupan':
            messages.error(request, 'Izabrani termin više nije dostupan. Izaberite drugi.')
            return redirect('customers:booking_form', salon_name=salon.name)

        try:
            appointment = Appointment.objects.create(
                salon=salon,
                time_slot=slot,
                customer=request.user,
                service=service,
                notes=notes,
                status='na čekanju'
            )

            owner_email = salon.owner.email
            if owner_email:
                try:
                    subject_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', '')
                    subject = f"{subject_prefix}Novi termin u salonu {salon.name}"
                    message_text = (
                        "Novi termin je zakazan.\n\n"
                        f"Salon: {salon.name}\n"
                        f"Klijent: {request.user.username}\n"
                        f"Usluga: {service.name}\n"
                        f"Datum: {slot.date.strftime('%d.%m.%Y')}\n"
                        f"Vreme: {slot.begin_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}\n"
                        f"Napomena: {notes if notes else '-'}\n"
                    )
                    message_html = f"""
                    <html>
                      <body style="font-family: Arial, sans-serif; color: #1F2937;">
                        <h2>Novi termin u salonu {salon.name}</h2>
                        <p><strong>Klijent:</strong> {request.user.username}</p>
                        <p><strong>Usluga:</strong> {service.name}</p>
                        <p><strong>Datum:</strong> {slot.date.strftime('%d.%m.%Y')}</p>
                        <p><strong>Vreme:</strong> {slot.begin_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}</p>
                        <p><strong>Napomena:</strong> {notes if notes else '-'}</p>
                      </body>
                    </html>
                    """

                    email_message = EmailMultiAlternatives(
                        subject,
                        message_text,
                        settings.DEFAULT_FROM_EMAIL,
                        [owner_email]
                    )
                    email_message.attach_alternative(message_html, 'text/html')
                    email_message.send(fail_silently=False)
                except Exception:
                    messages.warning(request, 'Termin je zakazan, ali slanje email obaveštenja nije uspelo.')

            messages.success(request, 'Termin je uspešno zakazan.')
            return redirect('customers:booking_form', salon_name=salon.name)
        except ValidationError as error:
            messages.error(request, error.message)
        except Exception:
            messages.error(request, 'Greška pri zakazivanju termina. Pokušajte ponovo.')

    context = {
        'salon': salon,
        'services': services,
        'today': date.today().isoformat(),
    }
    return render(request, 'customers/appointment_form.html', context)


@login_required
def available_slots(request, salon_name):
    if not _is_customer(request.user):
        return JsonResponse({'error': 'Nemate dozvolu.'}, status=403)

    salon = get_object_or_404(Salon, name=salon_name, is_approved=True, is_active=True)
    date_str = request.GET.get('date')

    if not date_str:
        return JsonResponse({'error': 'Datum je obavezan.'}, status=400)

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Neispravan format datuma.'}, status=400)

    generate_time_slots_for_date(salon, target_date)

    slots = TimeSlot.objects.filter(
        salon=salon,
        date=target_date,
        status='dostupan',
        appointment__isnull=True
    ).order_by('begin_time')

    slots_data = [
        {
            'id': slot.id,
            'label': f"{slot.begin_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        }
        for slot in slots
    ]

    return JsonResponse({'slots': slots_data})


@login_required
def my_appointments(request):
    """Prikaži sve termine korisnika (prethodne i buduće)"""
    if not _is_customer(request.user):
        messages.error(request, 'Samo mušterije mogu pristupiti svojim terminima.')
        return redirect('redirect_after_login')

    today = date.today()
    
    # Učitaj sve termine korisnika sortirane po datumu
    appointments = Appointment.objects.filter(
        customer=request.user
    ).select_related('time_slot', 'service', 'salon').order_by(
        '-time_slot__date', '-time_slot__begin_time'
    )
    
    # Razdvoji na buduće i prethodne
    future_appointments = []
    past_appointments = []
    
    for appointment in appointments:
        if appointment.time_slot.date >= today:
            future_appointments.append(appointment)
        else:
            past_appointments.append(appointment)
    
    context = {
        'future_appointments': future_appointments,
        'past_appointments': past_appointments,
        'today': today,
    }
    
    return render(request, 'customers/my_appointments.html', context)
