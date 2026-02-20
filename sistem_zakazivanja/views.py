from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.urls import reverse
from .forms import RegistrationForm, CustomLoginForm, UserEditForm
from .models import UserProfile
from salons.models import Salon


EMAIL_VERIFY_SALT = 'email-verify-v1'
EMAIL_VERIFY_MAX_AGE_SECONDS = 60 * 60 * 24


def _build_email_verification_token(user, email, purpose):
    payload = {
        'user_id': user.id,
        'email': email,
        'purpose': purpose,
    }
    return signing.dumps(payload, salt=EMAIL_VERIFY_SALT)


def _send_verification_email(request, user, email, purpose):
    token = _build_email_verification_token(user, email, purpose)
    verify_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )

    subject_prefix = getattr(settings, 'EMAIL_SUBJECT_PREFIX', '')
    subject = f"{subject_prefix}Potvrda email adrese"
    body_text = (
        f"Zdravo, {user.username}!\n\n"
        f"Kliknite na sledeći link da potvrdite email adresu:\n{verify_url}\n\n"
        "Ako niste vi tražili ovu izmenu, slobodno ignorišite poruku."
    )
    body_html = f"""
    <html>
      <body style=\"font-family: Arial, sans-serif; color: #1F2937;\">
        <h2>Potvrdite vašu email adresu</h2>
        <p>Zdravo, <strong>{user.username}</strong>!</p>
        <p>Kliknite na dugme ispod da potvrdite email adresu:</p>
        <p style=\"margin: 20px 0;\">
          <a href=\"{verify_url}\" style=\"background:#6366F1;color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;display:inline-block;\">Potvrdi email</a>
        </p>
        <p>Ili otvorite ovaj link ručno:</p>
        <p><a href=\"{verify_url}\">{verify_url}</a></p>
      </body>
    </html>
    """

    message = EmailMultiAlternatives(
        subject,
        body_text,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    message.attach_alternative(body_html, 'text/html')
    message.send(fail_silently=False)


def verify_email(request, token):
    try:
        payload = signing.loads(token, salt=EMAIL_VERIFY_SALT, max_age=EMAIL_VERIFY_MAX_AGE_SECONDS)
    except SignatureExpired:
        messages.error(request, 'Link za potvrdu email adrese je istekao.')
        return redirect('login')
    except BadSignature:
        messages.error(request, 'Link za potvrdu email adrese nije validan.')
        return redirect('login')

    user_id = payload.get('user_id')
    email = payload.get('email')
    purpose = payload.get('purpose')

    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if purpose == 'register':
        if user.email != email:
            messages.error(request, 'Email adresa za potvrdu se ne poklapa.')
            return redirect('login')

        profile.email_verified = True
        profile.pending_email = ''
        profile.save(update_fields=['email_verified', 'pending_email'])
        messages.success(request, 'Email adresa je uspešno potvrđena. Sada možete da se ulogujete.')
        return redirect('login')

    if purpose == 'change':
        if profile.pending_email != email:
            messages.error(request, 'Nema aktivnog zahteva za ovu email adresu.')
            return redirect('login')

        user.email = email
        user.save(update_fields=['email'])
        profile.email_verified = True
        profile.pending_email = ''
        profile.save(update_fields=['email_verified', 'pending_email'])
        messages.success(request, 'Nova email adresa je uspešno potvrđena. Sada možete da se ulogujete.')
        return redirect('login')

    messages.error(request, 'Nepoznata vrsta verifikacije email adrese.')
    return redirect('login')


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

            profile, _ = UserProfile.objects.get_or_create(user=user)
            if not profile.email_verified:
                target_email = profile.pending_email if profile.pending_email else user.email
                verify_purpose = 'change' if profile.pending_email else 'register'
                try:
                    _send_verification_email(request, user, target_email, purpose=verify_purpose)
                    messages.info(request, 'Email nije potvrđen. Poslali smo verifikacioni link.')
                except Exception:
                    messages.error(request, 'Email nije potvrđen, a slanje verifikacionog linka trenutno nije uspelo.')
                return render(request, 'login_page.html', {'form': form})

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

    if not profile.email_verified:
        logout(request)
        messages.error(request, 'Morate potvrditi email adresu pre nastavka.')
        return redirect('login')
    
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
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.email_verified = False
                profile.pending_email = ''
                profile.save(update_fields=['email_verified', 'pending_email'])

                _send_verification_email(request, user, user.email, purpose='register')
                messages.success(request, 'Nalog je uspešno kreiran.')
                messages.info(request, 'Poslali smo verifikacioni link na email. Potvrdite adresu pa se ulogujte.')
                return redirect('login')
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

    if not profile.email_verified:
        logout(request)
        messages.error(request, 'Morate potvrditi email adresu pre izbora uloge.')
        return redirect('login')

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


@login_required
def userEditForm(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            user = form.save()
            if getattr(form, 'password_changed', False):
                update_session_auth_hash(request, user)

            if getattr(form, 'email_change_requested', False):
                try:
                    _send_verification_email(request, user, form.pending_email, purpose='change')
                except Exception:
                    messages.error(request, 'Nije uspelo slanje verifikacionog linka na novu email adresu.')
                    return redirect('user_edit')

                logout(request)
                messages.info(request, 'Poslali smo verifikacioni link na novu email adresu. Potvrdite email pa se ponovo ulogujte.')
                return redirect('login')

            messages.success(request, 'Podaci profila su uspešno ažurirani.')
            return redirect('user_edit')
        messages.error(request, 'Molimo vas ispravite greške u formi.')
    else:
        form = UserEditForm(instance=request.user, user=request.user)

    return render(request, 'edit_user.html', {'form': form})