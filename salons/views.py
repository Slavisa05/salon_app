from django.shortcuts import render

# Create your views here.
def salon_dashboard(request):
    return render(request, 'salons/dashboard.html')