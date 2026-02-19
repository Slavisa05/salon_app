from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from sistem_zakazivanja.models import UserProfile


class CustomLoginForm(AuthenticationForm):    
    username = forms.CharField(
        label='Korisničko ime',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Korisničko ime',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Lozinka',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lozinka'
        })
    )

class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        label='Korisničko ime',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Korisničko ime'
        })
    )

    email = forms.EmailField(
        required=True,
        label='Email adresa',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email adresa'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Ime',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ime'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Prezime',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prezime'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Telefon',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Broj telefona (opciono)'
        })
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'password1',
            'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Korisničko ime'
            }),
        }
        labels = {
            'username': 'Korisničko ime',
            'email': 'Email adresa',
            'first_name': 'Ime',
            'last_name': 'Prezime',
            'phone': 'Telefon',
        }
    

    def __init__(self, *args, **kwargs):
        """Dodaj CSS klase na password polja"""
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Lozinka'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Potvrdi lozinku'
        })
        self.fields['password1'].label = 'Lozinka'
        self.fields['password2'].label = 'Potvrda lozinke'
    
    
    def save(self, commit=True):
        """
        Sačuvaj korisnika i ažuriraj UserProfile
        """
        # Kreiraj User objekat, ali ga ne čuvaj u bazu još
        user = super().save(commit=False)
        
        # Dodaj dodatne podatke
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            # Sačuvaj User u bazu
            user.save()
            
            # Signal je automatski kreirao UserProfile
            # Sada ažuriraj phone u profilu
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.save()
        
        return user
    

class UserEditForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        label='Telefon',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Broj telefona (opciono)'
        })
    )

    old_password = forms.CharField(
        required=False,
        label='Trenutna lozinka',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Unesite trenutnu lozinku'
        })
    )

    new_password1 = forms.CharField(
        required=False,
        label='Nova lozinka',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Unesite novu lozinku'
        })
    )

    new_password2 = forms.CharField(
        required=False,
        label='Potvrda nove lozinke',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Potvrdite novu lozinku'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Korisničko ime',
            'email': 'Email adresa',
            'first_name': 'Ime',
            'last_name': 'Prezime',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Korisničko ime'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email adresa'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ime'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prezime'}),
        }
        error_messages = {
            'username': {
                'required': 'Unesite korisničko ime.',
            },
            'email': {
                'required': 'Unesite email adresu.',
                'invalid': 'Unesite ispravnu email adresu.',
            },
            'first_name': {
                'required': 'Unesite ime.',
            },
            'last_name': {
                'required': 'Unesite prezime.',
            },
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user or self.instance

        if self.user and getattr(self.user, 'pk', None):
            profile, _ = UserProfile.objects.get_or_create(user=self.user)
            self.fields['phone'].initial = profile.phone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Korisničko ime je već zauzeto.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email adresa je već zauzeta.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        wants_password_change = bool(old_password or new_password1 or new_password2)

        if not wants_password_change:
            return cleaned_data

        if not old_password:
            self.add_error('old_password', 'Unesite trenutnu lozinku.')
        elif not self.instance.check_password(old_password):
            self.add_error('old_password', 'Trenutna lozinka nije tačna.')

        if not new_password1:
            self.add_error('new_password1', 'Unesite novu lozinku.')

        if not new_password2:
            self.add_error('new_password2', 'Potvrdite novu lozinku.')

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', 'Nova lozinka i potvrda se ne poklapaju.')

        if new_password1 and not self.errors.get('new_password1') and not self.errors.get('new_password2'):
            try:
                validate_password(new_password1, self.instance)
            except ValidationError as error:
                self.add_error('new_password1', error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        self.password_changed = False

        new_password = self.cleaned_data.get('new_password1')
        if new_password:
            user.set_password(new_password)
            self.password_changed = True

        if commit:
            user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = self.cleaned_data.get('phone', '')

        if commit:
            profile.save()

        return user