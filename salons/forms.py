from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from .models import Salon, Service, SalonWorkingHours


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