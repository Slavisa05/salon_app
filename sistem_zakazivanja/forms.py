from django import forms
from salons.models import Appointment, Service, TimeSlot
from datetime import date as date_type

class CustomerAppointment(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date_type.today().isoformat(),
        }),
        label='Datum'
    )
    
    class Meta:
        model = Appointment
        fields = ['service', 'time_slot', 'guest_name', 'guest_email', 'guest_phone', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'time_slot': forms.HiddenInput(),
            'guest_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Puno ime',
                'required': True
            }),
            'guest_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@primer.com',
                'required': True
            }),
            'guest_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+381 60 123 4567',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dodatne napomene (opciono)...'
            }),
        }
        labels = {
            'service': 'Izaberite uslugu',
            'guest_name': 'Ime i prezime',
            'guest_email': 'Email adresa',
            'guest_phone': 'Broj telefona',
            'notes': 'Napomena',
        }
    
    def __init__(self, *args, salon=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if salon:
            self.fields['service'].queryset = Service.objects.filter(
                salon=salon
            )
        
        # Ako je korisnik ulogovan, popuni podatke automatski
        if user and user.is_authenticated:
            self.fields['guest_name'].initial = user.get_full_name()
            self.fields['guest_email'].initial = user.email

            # self.fields['guest_name'].widget.attrs['readonly'] = True
            # self.fields['guest_email'].widget.attrs['readonly'] = True
    
    def clean_guest_phone(self):
        phone = self.cleaned_data.get('guest_phone')
        
        if not phone:
            return phone
        
        # Ukloni sve što nije cifra ili +
        phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Validacija: Mora imati bar 9 cifara (bez +)
        digits_only = phone_clean.replace('+', '')
        if len(digits_only) < 9:
            raise forms.ValidationError('Broj telefona mora imati najmanje 9 cifara.')
        
        # Opciono: Proveri format za Srbiju
        if digits_only.startswith('0'):
            # Lokalni format: 0601234567
            if len(digits_only) < 9 or len(digits_only) > 10:
                raise forms.ValidationError('Unesite validan srpski broj telefona.')
        elif phone_clean.startswith('+381'):
            # Međunarodni format: +381601234567
            if len(digits_only) < 11 or len(digits_only) > 12:
                raise forms.ValidationError('Unesite validan srpski broj telefona.')
        
        # Vrati normalizovan broj (sa + ako postoji, bez razmaka/crtica)
        return phone_clean
    
    def clean_time_slot(self):
        time_slot = self.cleaned_data.get('time_slot')
        
        if not time_slot:
            raise forms.ValidationError('Molimo izaberite termin.')
        
        if time_slot.status != 'dostupan':
            raise forms.ValidationError('Izabrani termin više nije dostupan.')
        
        # Dodatna provera da nema OneToOne conflict
        if hasattr(time_slot, 'appointment') and time_slot.appointment:
            if not self.instance.pk or time_slot.appointment.pk != self.instance.pk:
                raise forms.ValidationError('Ovaj termin je upravo zauzet.')
        
        return time_slot