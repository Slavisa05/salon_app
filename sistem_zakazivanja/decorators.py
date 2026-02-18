from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from salons.models import Salon
from .models import UserProfile

def require_barber_with_approved_salon(view_func):
    '''
    Dekorator koji proverava:
        - korisnik koji je ulogovan
        - korisnik koji je frizer
        - korisnik ima salon
        - salon je odobren
    '''

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Morate biti ulogovani.')
            return redirect('login')

        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        if profile.role != 'frizer':
            messages.error(request, 'Samo frizeri mogu pristupiti ovoj stranici.')
            return redirect('customers:home')
        
        try:
            salon = Salon.objects.get(owner=request.user)
        except Salon.DoesNotExist:
            messages.warning(request, 'Prvo kreirajte svoj salon.')
            return redirect('salons:create_salon')
        
        if not salon.is_approved:
            messages.info(request, 'Vaš salon čeka odobrenje administratora.')
            return redirect('pending_approval')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper 