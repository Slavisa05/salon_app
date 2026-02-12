from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from datetime import date, timedelta, datetime
from django.contrib import messages
from .models import Salon, TimeSlot, Appointment
from .utils import generate_time_slots_for_date
from .forms import SalonForm 


def salon_dashboard(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    return render(request, 'salons/dashboard.html', {'salon': salon})


def services_page(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    return render(request, 'salons/services.html', {'salon': salon})


def appointments_page(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    today = date.today()

    context = {
        'salon': salon,
        'today': today,
    }

    return render(request, 'salons/appointments.html', context)

def get_slots_for_date(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)
    date_str = request.GET.get('date')

    try: 
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
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


@require_POST
def block_slot(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    if hasattr(slot, 'appointment'):
        return JsonResponse({'error': 'Slot already has appointment'}, status=400)

    slot.status = 'blokiran'
    slot.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


@require_POST
def unblock_slot(request, salon_name, slot_id):
    salon = get_object_or_404(Salon, name=salon_name)
    slot = get_object_or_404(TimeSlot, id=slot_id, salon=salon)

    if hasattr(slot, 'appointment'):
        return JsonResponse({'error': 'Slot already has appointment'}, status=400)

    slot.status = 'dostupan'
    slot.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


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
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    service_name = appointment.service.name if appointment.service else None

    return JsonResponse({
        'customer': appointment.customer.username,
        'service': service_name,
        'status': appointment.status,
        'notes': appointment.notes,
        'date': slot.date.strftime('%Y-%m-%d'),
        'time': f"{slot.begin_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
    })


@require_POST
def cancel_appointment(request, salon_name, slot_id):
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
        return JsonResponse({'error': 'Appointment not found'}, status=404)

    if appointment.status == 'otkazano':
        return JsonResponse({'status': 'ok'})

    appointment.status = 'otkazano'
    appointment.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})


@login_required
def create_salon(request):
    if hasattr(request.user, 'salon'):
        return redirect('salon:salon_dashboard', salon_name=request.user.salon.name)

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                salon = form.save(commit=False)
                salon.owner = request.user
                salon.save()

                messages.success(request, f'Salon "{salon.name}" created successfully!')
                return redirect('salon:salon_dashboard', salon_name=salon.name)
            except Exception as e:
                messages.error(request, f'Error creating salon: {str(e)}')
    else:
        form = SalonForm()

    return render(request, 'salons/salon_form.html', {'form': form})


@login_required
def edit_salon(request, salon_name):
    salon = get_object_or_404(Salon, name=salon_name)

    if salon.owner != request.user:
        return HttpResponseForbidden("You don't have permission to edit this salon")

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES, instance=salon)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Salon "{salon.name}" updated successfully!')
                return redirect('salon:salon_dashboard', salon_name=salon.name)
            except Exception as e:
                messages.error(request, f'Error updating salon: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SalonForm(instance=salon)

    return render(request, 'salons/salon_form.html', {'form': form, 'salon': salon})