from datetime import date, datetime, timedelta, time
from .models import SalonWorkingHours, TimeSlot


def create_default_working_hours(salon):
    """
    Kreira default radno vreme za salon:
    Pon-Pet: 09:00-17:00 (radi)
    Sub-Ned: Ne radi
    """
    days_config = [
        {'day': 'ponedeljak', 'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'utorak', 'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'sreda', 'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'cetvrtak', 'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'petak', 'is_working': True, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'subota', 'is_working': False, 'opening': time(9, 0), 'closing': time(17, 0)},
        {'day': 'nedelja', 'is_working': False, 'opening': time(9, 0), 'closing': time(17, 0)},
    ]
    
    for config in days_config:
        SalonWorkingHours.objects.create(
            salon=salon,
            day=config['day'],
            is_working=config['is_working'],
            opening_time=config['opening'],
            closing_time=config['closing']
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
    day_mapping = {
        'monday': 'ponedeljak',
        'tuesday': 'utorak',
        'wednesday': 'sreda',
        'thursday': 'cetvrtak',
        'friday': 'petak',
        'saturday': 'subota',
        'sunday': 'nedelja'
    }
    
    serbian_day = day_mapping.get(day_name)
    
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
    
    # 3. Generiši sve slotove od opening do closing (svakih 30min)
    slots = []
    current_time = datetime.combine(target_date, working_hours.opening_time)
    end_time = datetime.combine(target_date, working_hours.closing_time)
    slot_duration = timedelta(minutes=30)
    
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
        day_mapping = {
            'monday': 'ponedeljak',
            'tuesday': 'utorak',
            'wednesday': 'sreda',
            'thursday': 'cetvrtak',
            'friday': 'petak',
            'saturday': 'subota',
            'sunday': 'nedelja'
        }
        
        if day_mapping[day_name] == changed_day:
            # Obriši samo DOSTUPNE slotove za taj dan
            TimeSlot.objects.filter(
                salon=salon,
                date=current_date,
                status='dostupan'
            ).delete()
            
            # Regeneriši slotove
            generate_time_slots_for_date(salon, current_date)
        
        current_date += timedelta(days=1)