from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, UserRole

@receiver(post_save, sender=User)
def create_user_profile_role(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)
        if not hasattr(instance, 'role'):
            UserRole.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile_role(sender, instance, **kwargs):
    instance.profile.save()
    instance.role.save()
