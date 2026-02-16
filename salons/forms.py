from django import forms
from .models import Salon, Service


class SalonForm(forms.ModelForm):
    class Meta:
        model = Salon
        fields = ['name', 'description', 'image', 'address', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Ime salona',
            'description': 'Opis salona',
            'image': 'Slika salona',
            'address': 'Adresa salona',
            'phone': 'Telefon salona',
        }

    
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