from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()
from .background_music import BackgroundMusic  # Sadece buradan çağrılıyor

from django.db import models
from django.conf import settings

class FavoriSalon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favori_salonlar')
    salon = models.ForeignKey('appointments.Salon', on_delete=models.CASCADE, related_name='favori_olanlar')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'salon']

    def __str__(self):
     return f"{self.user.username} ♥ {self.post}"


from django.db import models
from django.utils.text import slugify
from django.core.validators import RegexValidator

class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="Şehir Adı")

    def __str__(self):
        return self.name

class Salon(models.Model):
    name = models.CharField(max_length=100, verbose_name='Salon Adı')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='salons')
    address = models.TextField(blank=True, verbose_name='Adres')

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Telefon numarası geçersiz.")
    phone = models.CharField(validators=[phone_regex], max_length=20, blank=True, verbose_name='İletişim Telefonu')

    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Salon'
        verbose_name_plural = 'Salonlar'

    def __str__(self):
        return f"{self.name} ({self.city.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city.name}")
        super().save(*args, **kwargs)

class Appointment(models.Model):
    CATEGORI_CHOICES = [
        ('kadın', 'Kadın'),
        ('erkek', 'Erkek'),
        ('cocuk', 'Çocuk'),
    ]

    customer_name = models.CharField("Müşteri Adı", max_length=100)
    phone_number = models.CharField("Telefon Numarası", max_length=20)
    salon_name = models.CharField("Salon Adı", max_length=100, blank=True)
    appointment_date = models.DateTimeField("Randevu Tarihi", default=timezone.now)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, null=True, verbose_name="Salon")
    whatsapp_izin = models.BooleanField("WhatsApp İzni", default=False)
    category = models.CharField("Kategori", max_length=10, choices=CATEGORI_CHOICES, default='kadın')

    class Meta:
        ordering = ["appointment_date"]

    def __str__(self):
        return f"{self.customer_name} @ {self.appointment_date:%d.%m.%Y %H:%M}"

    def is_past_due(self):
        return timezone.now() > self.appointment_date

from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class ReelPost(models.Model):
    salon = models.ForeignKey('appointments.Salon', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    caption = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.salon.name} - {self.created_at.date()}"

    def total_likes(self):
        return self.reellike_set.count()

    def total_comments(self):
        return self.reelcomment_set.count()

    def first_media(self):
        return self.media.first()

# appointments/models.py
from django.db import models
from django.conf import settings
from .models import ReelPost

#from .models import SalonComment, Appointment, Salon, SalonMedia, BackgroundMusic, ReelPost, ReelComment

class SalonComment(models.Model):
    salon = models.ForeignKey('Salon', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.comment

class AIAnalysisLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    salon = models.ForeignKey("appointments.Salon", on_delete=models.CASCADE, null=True, blank=True)
    gun = models.CharField(max_length=20)
    saat = models.CharField(max_length=10)
    tahmin_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tahmin_tarihi']

    def __str__(self):
        return f"{self.user.username} için AI Tahmini: {self.gun} - {self.saat}"

class ReelLike(models.Model):
    post = models.ForeignKey(ReelPost, related_name='reellike_set', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
# appointments/models.py

class ReelComment(models.Model):
    post = models.ForeignKey(ReelPost, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()  # ← BU SATIR OLMALI
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.text[:30]}"


from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

# models.py
from django.db import models

# ReelsMedia modelinin varlığını koruyoruz
class ReelsMedia(models.Model):
    post = models.ForeignKey('ReelPost', on_delete=models.CASCADE, related_name='media')
    media_file = models.FileField(upload_to='reels/')
    type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.post.id}"

# SalonMedia modelini ekliyoruz
class SalonMedia(models.Model):
    post = models.ForeignKey('SalonPost', on_delete=models.CASCADE, related_name='media')
    media_file = models.FileField(upload_to='salon_media/')
    type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.post.id}"

from datetime import timedelta
from django.db import models

class AnlikPaylasim(models.Model):
    salon = models.ForeignKey('appointments.Salon', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    muzik = models.FileField(upload_to="music/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        return timezone.now() < self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"{self.salon.name} - {self.created_at.date()}"

class SalonPost(models.Model):
    salon = models.ForeignKey('Salon', on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100, blank=True, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Paylaşım Tarihi")

    def __str__(self):
        return f"{self.salon.name} - {self.title or 'Başlıksız'} ({self.created_at:%d.%m.%Y})"

    def first_media(self):
        return self.media.first()  # SalonMedia ile ilişkili medya var ise ilkini döndürür

    def total_media(self):
        return self.media.count()
