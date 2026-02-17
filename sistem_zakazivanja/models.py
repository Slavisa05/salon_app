from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('frizer', 'frizer'),
        ('musterija', 'musterija'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role or 'No role'}"
    

# SIGNALS
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatski kreiraj UserProfile kada se User kreira"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatski sačuvaj UserProfile kada se User sačuva"""
    UserProfile.objects.get_or_create(user=instance)
    instance.userprofile.save()