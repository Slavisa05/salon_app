from datetime import datetime, timedelta, date
from .models import TimeSlot, SalonWorkingHours

def generate_time_slots_for_date(salon, target_date):
    """
    Generiše sve moguće time slotove za salon na određeni datum
    """
    # 1. Odredi dan u nedelji (ponedeljak, utorak...)
    day_name = target_date.strftime('%A').lower()  # 'monday'
    day_mapping = {
        'monday': 'ponedeljak',
        'tuesday': 'utorak',
        'wednesday': 'sreda',
        'thursday': 'cetvrtak',
        'friday': 'petak',
        'saturday': 'subota',
        'sunday': 'nedelja'
    }
    
    # 2. Proveri da li salon radi tog dana
    try:
        working_hours = SalonWorkingHours.objects.get(
            salon=salon,
            day=day_mapping[day_name],
            is_working=True
        )
    except SalonWorkingHours.DoesNotExist:
        return [] 
    
    # 3. Generiši sve slotove od opening do closing time (svakih 30min)
    slots = []
    current_time = datetime.combine(target_date, working_hours.opening_time)
    end_time = datetime.combine(target_date, working_hours.closing_time)
    slot_duration = timedelta(minutes=30)
    
    while current_time + slot_duration <= end_time:
        slot_end = current_time + slot_duration
        
        # 4. Proveri da li slot već postoji u bazi
        existing_slot = TimeSlot.objects.filter(
            salon=salon,
            date=target_date,
            begin_time=current_time.time()
        ).first()
        
        if existing_slot:
            slots.append(existing_slot)
        else:
            # Kreiraj i sacuvaj slot da bi imao ID
            slot = TimeSlot.objects.create(
                salon=salon,
                date=target_date,
                begin_time=current_time.time(),
                end_time=slot_end.time(),
                status='dostupan'
            )
            slots.append(slot)
        
        current_time += slot_duration
    
    return slots
