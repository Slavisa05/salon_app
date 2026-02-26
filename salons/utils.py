from datetime import date, datetime, timedelta, time
from .models import SalonWorkingHours, TimeSlot, Appointment


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

def get_free_slots_for_day(salon, target_date, slot_minutes=30):
    # 1. Proveri da li salon radi tog dana
    day_name = target_date.strftime('%A').lower()
    serbian_day = DAY_MAPPING.get(day_name)
    try:
        wh = SalonWorkingHours.objects.get(salon=salon, day=serbian_day, is_working=True)
    except SalonWorkingHours.DoesNotExist:
        return []

    # 2. Generiši sve slotove u radnom vremenu
    slots = []
    start_dt = datetime.combine(target_date, wh.opening_time)
    end_dt = datetime.combine(target_date, wh.closing_time)
    slot_duration = timedelta(minutes=slot_minutes)
    while start_dt + slot_duration <= end_dt:
        slots.append( (start_dt.time(), (start_dt + slot_duration).time()) )
        start_dt += slot_duration

    # 3. Skupi sve zauzete i blokirane slotove
    blocked = list(TimeSlot.objects.filter(
        salon=salon,
        date=target_date,
        status='blokiran'
    ))
    reserved = list(Appointment.objects.filter(
        salon=salon,
        time_slot__date=target_date
    ).exclude(status='otkazano'))

    # map blokiranih i zauzetih po (start, end)
    slot_map = {}  # (start, end): {"status":..., "id":...}
    for slot in blocked:
        slot_map[(slot.begin_time, slot.end_time)] = {"status": "blokiran", "id": slot.id}
    for appt in reserved:
        slot_map[(appt.time_slot.begin_time, appt.time_slot.end_time)] = {"status": "zauzet", "id": appt.time_slot.id}
    
    # 4. Kreiraj listu za response
    free_slots = []
    for start, end in slots:
        key = (start, end)
        if key in slot_map:
            slot = slot_map[key]
            free_slots.append({
                "begin_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "status": slot["status"],
                "id": slot["id"]
            })
        else:
            free_slots.append({
                "begin_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "status": "dostupan",
                "id": None
            })
            
    return free_slots