from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, CustomLoginForm
from .models import UserProfile


def landing(request):
    return render(request, 'landing.html')


def login_page(request):    
    if request.user.is_authenticated:
        messages.info(request, 'Već ste ulogovani.')
        return redirect('customers:home')
    
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        
        if form.is_valid():
            user = form.get_user() 
            login(request, user)
            messages.success(request, f'Dobrodošli nazad, {user.username}!')
            return redirect('customers:home')
        else:
            messages.error(request, 'Molimo ispravite greške u formi.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'login_page.html', {'form': form})


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
        return redirect('customers:home')
    
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
            return redirect('salon:create_salon')
    

    return render(request, 'choose_role.html')
