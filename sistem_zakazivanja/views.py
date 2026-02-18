from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, CustomLoginForm
from .models import UserProfile
from salons.models import Salon


def landing(request):
    return render(request, 'landing.html')


def login_page(request):    
    if request.user.is_authenticated:
        messages.info(request, 'Već ste ulogovani.')
        return redirect('redirect_after_login')
    
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        
        if form.is_valid():
            user = form.get_user() 
            login(request, user)
            messages.success(request, f'Dobrodošli nazad, {user.username}!')
            return redirect('redirect_after_login')
        else:
            messages.error(request, 'Molimo ispravite greške u formi.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'login_page.html', {'form': form})


@login_required
def redirect_after_login(request):
    """Pametna redirekcija nakon login-a"""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if user.is_superuser or user.is_staff:
        return redirect('admin:index')

    if not profile.role:
        return redirect('choose_role')
    
    if profile.role == 'musterija':
        return redirect('customers:home')
    
    if profile.role == 'frizer':
        try:
            salon = Salon.objects.get(owner=user)
            
            if not salon.is_approved:
                messages.info(request, 'Vaš salon još uvek čeka odobrenje.')
                return redirect('pending_approval')
            
            messages.success(request, f'Dobrodošli nazad, {user.username}!')
            return redirect('salons:salon_dashboard', salon_name=salon.name)
        
        except Salon.DoesNotExist:
            messages.warning(request, 'Prvo kreirajte svoj salon.')
            return redirect('salons:create_salon')
    
    # Fallback
    return redirect('customers:home')


def register_page(request):
    if request.user.is_authenticated:
        messages.info(request, 'Već ste ulogovani.')
        return redirect('customers:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Dobrodošli, {user.username}! Nalog je uspešno kreiran.')
                return redirect('choose_role')
            except Exception as e:
                messages.error(request, f'Greška pri kreiranju naloga: {str(e)}')
        else:
            messages.error(request, 'Molimo ispravite greške u formi.')
    else:
        form = RegistrationForm()

    return render(request, 'register_page.html', {'form': form})
        

@login_required
def choose_role(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role:
        messages.info(request, 'Vec ste izabrali ulogu...')
        return redirect('redirect_after_login')
    
    if request.method == 'POST':
        role = request.POST.get('role')
        if role == 'customer':
            role = 'musterija'
        
        if role not in ['musterija', 'frizer']:
            messages.error(request, 'Izaberite odgovarajuci role')
            return redirect('choose_role')
        
        profile.role = role
        profile.save()
        
        if role == 'musterija':
            messages.success(request, 'Uspešno ste se registrovali!')
            return redirect('customers:home')
        else:  
            messages.info(request, 'Pravljenje salona...')
            return redirect('salons:create_salon')
    

    return render(request, 'choose_role.html')


@login_required
def pending_approval_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if profile.role != 'frizer':
        messages.info(request, 'Ova stranica je samo za frizere.')
        return redirect('home')

    try:
        salon = Salon.objects.get(owner=request.user)
    except Salon.DoesNotExist:
        return redirect("create_salon")

    if salon.is_approved:
        return redirect("dashboard")

    return render(request, "pending_approval.html", {"salon": salon})
