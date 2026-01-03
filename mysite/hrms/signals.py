from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, Payroll


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create Profile and Payroll when a new user is created"""
    if created:
        # Create profile if it doesn't exist
        if not hasattr(instance, 'profile'):
            Profile.objects.create(
                user=instance,
                designation='Not Assigned',
                department='Not Assigned'
            )
        
        # Create default payroll if it doesn't exist
        if not Payroll.objects.filter(user=instance).exists():
            Payroll.objects.create(
                user=instance,
                basic_salary=0.00
            )


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save profile whenever user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
