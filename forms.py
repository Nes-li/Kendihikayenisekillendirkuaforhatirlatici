from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from .models import Appointment, SalonMedia, ReelComment
from datetime import datetime

# appointments/forms.py
from django import forms

class SalonMediaForm(forms.Form):
    media_files = forms.FileField(
        required=False,
        label="Dosya Seçin"
    )


# --- RANDEVU FORMU ---
class AppointmentForm(forms.ModelForm):
    appointment_date = forms.DateTimeField(
        label='Randevu Tarihi ve Saati',
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'customer_name', 'phone_number']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'customer_name': 'Müşteri Adı',
            'phone_number': 'Telefon Numarası',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        tahmin = kwargs.pop('tahmin', None)
        super().__init__(*args, **kwargs)

        if tahmin:
            if isinstance(tahmin, str):
                try:
                    tahmin_dt = datetime.strptime(tahmin, '%Y-%m-%d %H:%M')
                except ValueError:
                    tahmin_dt = None
            elif isinstance(tahmin, datetime):
                tahmin_dt = tahmin
            else:
                tahmin_dt = None

            if tahmin_dt:
                self.fields['appointment_date'].initial = tahmin_dt.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('appointment_date')

        if self.user and date:
            salon = getattr(self.user, 'salon', None)
            if not salon:
                salon = self.user.salon_set.first()
            if Appointment.objects.filter(appointment_date=date, salon=salon).exists():
                raise ValidationError("Seçtiğiniz saat zaten dolu. Lütfen başka bir saat seçin.")

# --- REEL YORUM FORMU ---
class ReelCommentForm(forms.ModelForm):
    class Meta:
        model = ReelComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Yorumunuzu yazın...'})
        }

# --- REEL YÜKLEME FORMU ---
class ReelUploadForm(forms.Form):
    caption = forms.CharField(
        label='Açıklama', max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    media_files = forms.FileField(
        required=False
    )

from django import forms
from .models import SalonComment

class SalonCommentForm(forms.ModelForm):
    class Meta:
        model = SalonComment
        fields = ['comment']   # *** Dikkat: 'comment' olacak! ***
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Yorumunuzu yazın...'})
        }

