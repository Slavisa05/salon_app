from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from sistem_zakazivanja.models import UserProfile


class CustomLoginForm(AuthenticationForm):    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Korisničko ime',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lozinka'
        })
    )


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email adresa'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ime'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prezime'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
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
            'username': 'Username',
            'email': 'Email',
            'first_name': 'Ime',
            'last_name': 'Prezime',
            'phone': 'Telefon',
            'password1': 'lozinka',
            'password2': 'potvrdite lozinku',
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