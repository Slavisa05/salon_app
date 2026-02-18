from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from datetime import date, timedelta, datetime
from django.contrib import messages
from sistem_zakazivanja.decorators import require_barber_with_approved_salon
from sistem_zakazivanja.models import UserProfile
from .models import Salon, TimeSlot, Appointment, Service
from .utils import generate_time_slots_for_date, create_default_working_hours, generate_slots_for_next_months, regenerate_future_slots_after_hours_change
from .forms import SalonForm, ServiceForm


@require_barber_with_approved_salon
def salon_dashboard(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da vidite dashboard ovog salona")
    
    # Filtriraj termine samo za danas i sortiraj po vremenu
    today = date.today()
    appointments = salon.appointments.filter(
        time_slot__date=today
    ).select_related('time_slot', 'service', 'customer').order_by('time_slot__begin_time').exclude(status='otkazano')

    return render(request, 'salons/dashboard.html', {'salon': salon, 'appointments': appointments})


@require_barber_with_approved_salon
def services_page(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da vidite stranicu za usluge ovog salon")
    
    services = salon.services.all()

    return render(request, 'salons/services.html', {'salon': salon, 'services': services})


@require_barber_with_approved_salon
def appointments_page(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    today = date.today()

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da vidite termine ovog salona")

    context = {
        'salon': salon,
        'today': today,
    }

    return render(request, 'salons/appointments.html', context)


@require_barber_with_approved_salon
def get_slots_for_date(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    date_str = request.GET.get('date')
    
    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da generišete slotove za ovaj salon!")

    try: 
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return JsonResponse({'error': 'Nevalidan format datuma'}, status=400)
    
    slots = generate_time_slots_for_date(salon, target_date)

    appointments = Appointment.objects.select_related('time_slot', 'service').filter(
        time_slot__salon=salon,
        time_slot__date=target_date
    ).exclude(status='otkazano')

    def get_slot_minutes(slot):
        start = datetime.combine(slot.date, slot.begin_time)
        end = datetime.combine(slot.date, slot.end_time)
        minutes = int((end - start).total_seconds() / 60)
        return minutes if minutes > 0 else 30

    def build_appointment_ranges():
        ranges = []
        for appointment in appointments:
            slot_minutes = get_slot_minutes(appointment.time_slot)
            duration = appointment.service.duration if appointment.service else slot_minutes
            start = datetime.combine(appointment.time_slot.date, appointment.time_slot.begin_time)
            end = start + timedelta(minutes=duration)
            ranges.append((start, end, appointment))
        return ranges

    appointment_ranges = build_appointment_ranges()

    # Konvertuj u JSON format
    slots_data = []
    for slot in slots:
        slot_start = datetime.combine(slot.date, slot.begin_time)
        slot_end = datetime.combine(slot.date, slot.end_time)
        overlapping_appointment = None

        for appointment_start, appointment_end, appointment in appointment_ranges:
            if slot_start < appointment_end and slot_end > appointment_start:
                overlapping_appointment = appointment
                break

        status = 'zauzet' if overlapping_appointment else slot.status
        has_appointment = bool(overlapping_appointment) or hasattr(slot, 'appointment')

        slots_data.append({
            'id': slot.id if slot.id else None,
            'begin_time': slot.begin_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'status': status,
            'has_appointment': has_appointment
        })
    
    return JsonResponse({'slots': slots_data})


@require_barber_with_approved_salon
@require_POST
def block_slot(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da blokirate slotove za ovaj salon")

    if hasattr(slot, 'appointment'):
        return JsonResponse({'error': 'Slot već ima termin'}, status=400)

    slot.status = 'blokiran'
    slot.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


@require_barber_with_approved_salon
@require_POST
def unblock_slot(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da odblokirate slotove za ovaj salon")

    if hasattr(slot, 'appointment'):
        return JsonResponse({'error': 'Slot već ima termin'}, status=400)

    slot.status = 'dostupan'
    slot.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


@require_barber_with_approved_salon
def appointment_details(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    appointment = None
    if hasattr(slot, 'appointment'):
        appointment = slot.appointment
    else:
        appointments = Appointment.objects.select_related('time_slot', 'service').filter(
            time_slot__salon=salon,
            time_slot__date=slot.date
        ).exclude(status='otkazano')

        slot_start = datetime.combine(slot.date, slot.begin_time)
        slot_end = datetime.combine(slot.date, slot.end_time)

        for candidate in appointments:
            slot_minutes = int(
                (datetime.combine(candidate.time_slot.date, candidate.time_slot.end_time) -
                 datetime.combine(candidate.time_slot.date, candidate.time_slot.begin_time)).total_seconds() / 60
            )
            slot_minutes = slot_minutes if slot_minutes > 0 else 30
            duration = candidate.service.duration if candidate.service else slot_minutes
            candidate_start = datetime.combine(candidate.time_slot.date, candidate.time_slot.begin_time)
            candidate_end = candidate_start + timedelta(minutes=duration)

            if slot_start < candidate_end and slot_end > candidate_start:
                appointment = candidate
                break

    if not appointment:
        return JsonResponse({'error': 'Termin nije pronađen'}, status=404)
    service_name = appointment.service.name if appointment.service else None

    return JsonResponse({
        'customer': appointment.customer.username,
        'service': service_name,
        'status': appointment.status,
        'notes': appointment.notes,
        'date': slot.date.strftime('%Y-%m-%d'),
        'time': f"{slot.begin_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
    })


@require_barber_with_approved_salon
@require_POST
def cancel_appointment(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da otkazujete termine za ovaj salon")

    appointment = None
    if hasattr(slot, 'appointment'):
        appointment = slot.appointment
    else:
        appointments = Appointment.objects.select_related('time_slot', 'service').filter(
            time_slot__salon=salon,
            time_slot__date=slot.date
        ).exclude(status='otkazano')

        slot_start = datetime.combine(slot.date, slot.begin_time)
        slot_end = datetime.combine(slot.date, slot.end_time)

        for candidate in appointments:
            slot_minutes = int(
                (datetime.combine(candidate.time_slot.date, candidate.time_slot.end_time) -
                 datetime.combine(candidate.time_slot.date, candidate.time_slot.begin_time)).total_seconds() / 60
            )
            slot_minutes = slot_minutes if slot_minutes > 0 else 30
            duration = candidate.service.duration if candidate.service else slot_minutes
            candidate_start = datetime.combine(candidate.time_slot.date, candidate.time_slot.begin_time)
            candidate_end = candidate_start + timedelta(minutes=duration)

            if slot_start < candidate_end and slot_end > candidate_start:
                appointment = candidate
                break

    if not appointment:
        return JsonResponse({'error': 'Termin nije pronađen'}, status=404)

    if appointment.status == 'otkazano':
        return JsonResponse({'status': 'ok'})

    appointment.status = 'otkazano'
    appointment.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


# SALON FORMS
@login_required
def create_salon(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role != 'frizer':
        messages.error(request, 'Samo frizeri mogu kreirati salone.')
        return redirect('home')

    try:
        salon = Salon.objects.get(owner=request.user)
        
        if not salon.is_approved:
            messages.info(request, 'Vaš salon već čeka odobrenje.')
            return redirect('pending_approval')
        else:
            messages.info(request, 'Već imate salon.')
            return redirect('salons:salon_dashboard', salon_name=salon.name)
    except Salon.DoesNotExist:
        pass

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                salon = form.save(commit=False)
                salon.owner = request.user
                salon.is_approved = False
                salon.is_active = False
                salon.save()


                messages.success(
                    request,
                    f'Salon "{salon.name}" je uspešno kreiran! '
                    f'Čeka se odobrenje administratora.'
                )

                return redirect('pending_approval')
            except Exception as e:
                messages.error(request, f'Greška pri kreiranju salona: {str(e)}')
    else:
        form = SalonForm()

    return render(request, 'salons/salon_form.html', {'form': form})


@require_barber_with_approved_salon
def edit_salon(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da menjate ovaj salon")

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES, instance=salon)
        if form.is_valid():
            try:
                form.save()
                
                messages.success(
                    request,
                    'Salon je ažuriran! '
                )
                return redirect('salons:edit_salon', salon_name=salon.name)
            except Exception as e:
                messages.error(request, f'Greška pri ažuriranju salona: {str(e)}')
        else:
            messages.error(request, 'Molimo vas ispravite greške ispod.')
    else:
        form = SalonForm(instance=salon)

    return render(request, 'salons/salon_form.html', {'form': form, 'salon': salon, 'is_edit': True})


# SERVICE FORMS
@require_barber_with_approved_salon
def create_service(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name, owner=request.user)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da dodajete usluge ovom salonu")
    
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            try:
                service = form.save(commit=False)
                service.salon = salon
                service.save()
                messages.success(request, f'Usluga "{service.name}" uspešno dodata!')
                return redirect('salons:services_page', salon_name=salon.name)
            except Exception as e:
                messages.error(request, f'Greška pri dodavanju usluge: {str(e)}')
        else:
            messages.error(request, 'Molimo vas ispravite greške ispod.')
    else:
        form = ServiceForm()

    context = {
        'form': form,
        'salon': salon,
        'is_editing': False,
    }
    return render(request, 'salons/service_form.html', context)


@require_barber_with_approved_salon
def update_service(request, salon_name, service_id):
    salon = get_object_or_404(Salon, name=salon_name, owner=request.user)
    service = get_object_or_404(Service, salon=salon, id=service_id)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da menjate usluge ovog salona")
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Usluga "{service.name}" uspešno ažurirana!')
                return redirect('salons:services_page', salon_name=salon.name)
            except Exception as e:
                messages.error(request, f'Greška pri ažuriranju usluge: {str(e)}')
        else:
            messages.error(request, 'Molimo vas ispravite greške ispod.')
    else:
        form = ServiceForm(instance=service)

    context = {
        'form': form,
        'salon': salon,
        'is_editing': True,
    }
    return render(request, 'salons/service_form.html', context)


@require_barber_with_approved_salon
def delete_service(request, salon_name, service_id):
    salon = get_object_or_404(Salon, name=salon_name, owner=request.user)
    service = get_object_or_404(Service, salon=salon, id=service_id)

    if not (request.user.is_superuser or request.user.is_staff):
        if salon.owner != request.user:
            return HttpResponseForbidden("Nemate dozvolu da brisete usluge ovog salona")
    
    try:
        service_name = service.name
        service.delete()
        messages.success(request, f'Usluga "{service_name}" uspešno obrisana!')
    except Exception as e:
        messages.error(request, f'Greška pri brisanju usluge: {str(e)}')
    
    return redirect('salons:services_page', salon_name=salon.name)
