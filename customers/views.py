from django.shortcuts import render, redirect, get_object_or_404
from salons.models import Salon

def home(request):
    salons = Salon.objects.all()

    return render(request, 'customers/home.html', {'salons': salons})
