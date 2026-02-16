from django.forms import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from datetime import datetime
from salons.models import Salon, Appointment, Service, TimeSlot
from .forms import CustomerAppointment

def landing_page(request):
    salons = Salon.objects.all()

    return render(request, 'landing.html', {'salons': salons})


def customer_appointment(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)

    if request.method == 'POST':
        form = CustomerAppointment(
            request.POST, 
            salon=salon, 
            user=request.user if request.user.is_authenticated else None
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    appointment = form.save(commit=False)
                    appointment.salon = salon
                    
                    # Poveži registrovanog korisnika
                    if request.user.is_authenticated:
                        appointment.customer = request.user
                    
                    appointment.status = 'pending'
                    
                    # save() metoda iz modela će automatski:
                    # 1. Validirati podatke (clean())
                    # 2. Označiti slotove kao zauzete
                    appointment.save()

                    recipient_email = (
                        appointment.customer.email
                        if appointment.customer and appointment.customer.email
                        else appointment.guest_email
                    )
                    
                    messages.success(
                        request, 
                        f'Uspešno ste zakazali termin za {appointment.time_slot.date} '
                        f'u {appointment.time_slot.begin_time}! '
                        f'Potvrda je poslata na {recipient_email}.'
                    )
                    return redirect('appointment_confirmation', appointment.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Došlo je do greške: {str(e)}')
        else:
            messages.error(request, 'Molimo ispravite greške u formi.')
    else:
        form = CustomerAppointment(
            salon=salon, 
            user=request.user if request.user.is_authenticated else None
        )
    
    services = salon.services.all()
    
    context = {
        'salon': salon,
        'form': form,
        'services': services,
    }

    return render(request, 'customer_appointment.html', context)


def appointment_confirmation(request, appointment_id):
    """Confirmation page posle bookinga"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'appointment_confirmation.html', context)


# ==============================================
# API
# ==============================================

def available_timeslots_api(request):
    """API endpoint za dostupne timeslots (AJAX)"""
    salon_id = request.GET.get('salon')
    date_str = request.GET.get('date')
    service_id = request.GET.get('service')
    
    try:
        salon = Salon.objects.get(id=salon_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (Salon.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Nevalidni parametri'}, status=400)
    
    # Preuzmi dostupne TimeSlot-ove
    timeslots = TimeSlot.objects.filter(
        salon=salon,
        date=date,
        status='dostupan'
    ).order_by('begin_time')
    
    # Formatuj rezultate
    data = [{
        'id': ts.id,
        'start_time': ts.begin_time.strftime('%H:%M'),
        'end_time': ts.end_time.strftime('%H:%M'),
    } for ts in timeslots]
    
    return JsonResponse({'timeslots': data})
        