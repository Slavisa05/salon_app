from django.shortcuts import render


def salon_dashboard(request):
    return render(request, 'salons/dashboard.html')


def services_page(request):
    return render(request, 'salons/services.html')