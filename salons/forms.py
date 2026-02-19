from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from .models import Salon, Service, SalonWorkingHours


class SalonScheduleForm(forms.Form):
    slot_interval_minutes = forms.ChoiceField(
        choices=[('15', 'Na 15 minuta'), ('30', 'Na 30 minuta'), ('60', 'Na 60 minuta')],
        label='Generisanje termina',
        initial='30',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, initial_hours=None, **kwargs):
        super().__init__(*args, **kwargs)
        initial_hours = initial_hours or {}

        for day_key, day_label in SalonWorkingHours.DAYS:
            day_initial = initial_hours.get(day_key, {})

            self.fields[f'{day_key}_is_working'] = forms.BooleanField(
                required=False,
                label=day_label,
                initial=day_initial.get('is_working', False),
                widget=forms.CheckboxInput(attrs={'class': 'working-day-checkbox'})
            )
            self.fields[f'{day_key}_opening_time'] = forms.TimeField(
                required=False,
                initial=day_initial.get('opening_time'),
                input_formats=['%H:%M', '%H:%M:%S'],
                widget=forms.TimeInput(
                    format='%H:%M',
                    attrs={'type': 'time', 'class': 'form-control working-time-input'}
                )
            )
            self.fields[f'{day_key}_closing_time'] = forms.TimeField(
                required=False,
                initial=day_initial.get('closing_time'),
                input_formats=['%H:%M', '%H:%M:%S'],
                widget=forms.TimeInput(
                    format='%H:%M',
                    attrs={'type': 'time', 'class': 'form-control working-time-input'}
                )
            )

    def clean(self):
        cleaned_data = super().clean()

        for day_key, day_label in SalonWorkingHours.DAYS:
            is_working = cleaned_data.get(f'{day_key}_is_working')
            opening_time = cleaned_data.get(f'{day_key}_opening_time')
            closing_time = cleaned_data.get(f'{day_key}_closing_time')

            if is_working:
                if not opening_time:
                    self.add_error(f'{day_key}_opening_time', f'Unesite vreme otvaranja za {day_label.lower()}.')
                if not closing_time:
                    self.add_error(f'{day_key}_closing_time', f'Unesite vreme zatvaranja za {day_label.lower()}.')
                if opening_time and closing_time and opening_time >= closing_time:
                    self.add_error(f'{day_key}_closing_time', f'Vreme zatvaranja mora biti nakon otvaranja za {day_label.lower()}.')

        return cleaned_data

    def get_hours_payload(self):
        payload = []

        for day_key, _ in SalonWorkingHours.DAYS:
            payload.append({
                'day': day_key,
                'is_working': self.cleaned_data.get(f'{day_key}_is_working', False),
                'opening_time': self.cleaned_data.get(f'{day_key}_opening_time'),
                'closing_time': self.cleaned_data.get(f'{day_key}_closing_time'),
            })

        return payload

    def get_day_rows(self):
        rows = []
        for day_key, day_label in SalonWorkingHours.DAYS:
            rows.append({
                'key': day_key,
                'label': day_label,
                'is_working': self[f'{day_key}_is_working'],
                'opening_time': self[f'{day_key}_opening_time'],
                'closing_time': self[f'{day_key}_closing_time'],
            })
        return rows


class SalonForm(forms.ModelForm):    
    class Meta:
        model = Salon
        fields = ['name', 'address', 'phone', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Naziv salona'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresa'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+381 60 123 4567'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis salona...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/jpg,image/png,image/webp',
                'id': 'id_image'
            }),
        }
        labels = {
            'image': 'Slika salona',
        }
    
    def clean_image(self):
        """Validacija slike"""
        image = self.cleaned_data.get('image')

        if not image:
            return image

        is_uploaded_file = hasattr(image, 'content_type')

        if not is_uploaded_file:
            return image
        
        # Proveri veličinu (5MB)
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Slika je prevelika. Maksimalno 5MB.')

        # Proveri tip
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if image.content_type not in valid_types:
            raise forms.ValidationError('Nevalidan format slike. Koristite JPG, PNG ili WebP.')

        try:
            uploaded_image = Image.open(image)
            width, height = uploaded_image.size
            image.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError('Datoteka nije validna slika.')

        if (width, height) != (500, 500):
            raise forms.ValidationError('Slika mora biti tačno 500x500 piksela.')
        
        return image
    
    
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'npr. fejd šišanje',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Fejd šišanje se sastoji iz...',
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={  
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'duration': forms.NumberInput(attrs={  
                'class': 'form-control',
                'min': '5',
                'step': '5',
                'placeholder': 'npr. 30, 60, 90...'
            }),
        }
        labels = {
            'name': 'Naziv usluge',
            'description': 'Opis usluge',
            'image': 'Cena usluge',
            'address': 'Trajanje usluge (u minutima)',
        }

        def clean_duration(self):
            duration = self.clean_data.get('duration')

            if duration and duration % 5 != 0:
                raise forms.ValidationError('Trajanje mora biti deljivo sa 5 minuta.')
            
            if duration and duration < 5:
                raise forms.ValidationError('Trajanje mora biti najmanje 5 minuta.')
            
            return duration
        
        def clean_price(self):
            price = self.cleaned_data.get('price')

            if price and price <= 0:
                raise forms.ValidationError('Cena mora biti veća od 0.')
            
            return price