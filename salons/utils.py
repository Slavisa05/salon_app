from datetime import date, datetime, timedelta, time
from .models import SalonWorkingHours, TimeSlot


DAY_MAPPING = {
    'monday': 'ponedeljak',
    'tuesday': 'utorak',
    'wednesday': 'sreda',
    'thursday': 'cetvrtak',
    'friday': 'petak',
    'saturday': 'subota',
    'sunday': 'nedelja'
}

DEFAULT_WORKING_HOURS = {
    'ponedeljak': {'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
    'utorak': {'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
    'sreda': {'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
    'cetvrtak': {'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
    'petak': {'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
    'subota': {'is_working': False, 'opening': time(9, 0), 'closing': time(17, 0)},
    'nedelja': {'is_working': False, 'opening': time(9, 0), 'closing': time(17, 0)},
}


def get_default_working_hours_map():
    return {
        day: {
            'is_working': data['is_working'],
            'opening_time': data['opening'],
            'closing_time': data['closing'],
        }
        for day, data in DEFAULT_WORKING_HOURS.items()
    }


def upsert_working_hours(salon, hours_payload):
    for item in hours_payload:
        day = item['day']
        is_working = item['is_working']
        opening = item['opening_time'] if item['opening_time'] else DEFAULT_WORKING_HOURS[day]['opening']
        closing = item['closing_time'] if item['closing_time'] else DEFAULT_WORKING_HOURS[day]['closing']

        SalonWorkingHours.objects.update_or_create(
            salon=salon,
            day=day,
            defaults={
                'is_working': is_working,
                'opening_time': opening,
                'closing_time': closing,
            }
        )


def create_default_working_hours(salon):
    """
    Kreira default radno vreme za salon:
    Pon-Pet: 09:00-17:00 (radi)
    Sub-Ned: Ne radi
    """
    for day, config in DEFAULT_WORKING_HOURS.items():
        SalonWorkingHours.objects.update_or_create(
            salon=salon,
            day=day,
            defaults={
                'is_working': config['is_working'],
                'opening_time': config['opening'],
                'closing_time': config['closing'],
            }
        )


def generate_slots_for_next_months(salon, months=2):
    """
    Generiše slotove za narednih X meseci od danas
    """
    start_date = date.today()
    end_date = start_date + timedelta(days=30 * months) 
    
    current_date = start_date
    
    while current_date <= end_date:
        generate_time_slots_for_date(salon, current_date)
        current_date += timedelta(days=1)


def generate_time_slots_for_date(salon, target_date):
    """
    Generiše sve moguće time slotove za salon na određeni datum
    """
    # 1. Odredi dan u nedelji
    day_name = target_date.strftime('%A').lower()
    serbian_day = DAY_MAPPING.get(day_name)
    
    # 2. Proveri da li salon radi tog dana
    try:
        working_hours = SalonWorkingHours.objects.get(
            salon=salon,
            day=serbian_day,
            is_working=True
        )
    except SalonWorkingHours.DoesNotExist:
        # Ne radi tog dana - ne generiši slotove
        return []
    
    # 3. Generiši sve slotove od opening do closing (svakih 15 ili 30 min)
    slots = []
    current_time = datetime.combine(target_date, working_hours.opening_time)
    end_time = datetime.combine(target_date, working_hours.closing_time)
    slot_minutes = getattr(salon, 'slot_interval_minutes', 30) or 30
    slot_duration = timedelta(minutes=slot_minutes)
    
    while current_time + slot_duration <= end_time:
        slot_end = current_time + slot_duration
        
        # 4. Proveri da li slot već postoji
        existing_slot = TimeSlot.objects.filter(
            salon=salon,
            date=target_date,
            begin_time=current_time.time()
        ).first()
        
        if existing_slot:
            slots.append(existing_slot)
        else:
            # Kreiraj novi slot
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


def add_one_day_slots(salon):
    """
    Dodaje slotove za jedan novi dan (2 meseca unapred od danas)
    Koristi se u daily task-u
    """
    target_date = date.today() + timedelta(days=60) 
    generate_time_slots_for_date(salon, target_date)


def regenerate_future_slots_after_hours_change(salon, changed_day):
    """
    Kada se promeni radno vreme, regeneriši buduće slotove za taj dan
    Briše samo DOSTUPNE slotove (ne dira zauzete termine)
    """
    today = date.today()
    end_date = today + timedelta(days=60)
    
    current_date = today
    
    while current_date <= end_date:
        # Proveri da li je ovaj dan u nedelji jednak promenjenom danu
        day_name = current_date.strftime('%A').lower()
        if DAY_MAPPING[day_name] == changed_day:
            # Obriši samo DOSTUPNE slotove za taj dan
            TimeSlot.objects.filter(
                salon=salon,
                date=current_date,
                status='dostupan'
            ).delete()
            
            # Regeneriši slotove
            generate_time_slots_for_date(salon, current_date)
        
        current_date += timedelta(days=1)


def regenerate_future_slots_all_days(salon):
    today = date.today()
    end_date = today + timedelta(days=60)

    current_date = today
    while current_date <= end_date:
        TimeSlot.objects.filter(
            salon=salon,
            date=current_date,
            status='dostupan'
        ).delete()
        generate_time_slots_for_date(salon, current_date)
        current_date += timedelta(days=1)