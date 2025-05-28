from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


# ✅ Yeni kullanıcı oluşturulduğunda otomatik profil oluşturan sinyal
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# ✅ Her kullanıcı güncellemesinde profilini de kaydeden sinyal
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
