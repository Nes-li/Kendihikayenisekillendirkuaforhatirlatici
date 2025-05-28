# Python standart kütüphaneleri
import os
import random
import zipfile
import tempfile
from io import BytesIO
from datetime import datetime, timedelta, time
from .forms import SalonMediaForm
import qrcode
from accounts.forms import RegisterForm
from django.views.decorators.csrf import csrf_protect


# 3rd-party (harici) kütüphaneler
import matplotlib.pyplot as plt
from xhtml2pdf import pisa
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .utils import tahmin_motoru
from .utils import tahmin_motoru
from .ai_utils import tahmin_motoru

# Django built-in
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.db.models.functions import ExtractHour
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from django.utils.timezone import localdate, make_aware, now
from django.utils.translation import gettext as _
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

# Uygulama içi
from .models import Appointment
from .utils import (
    tahmini_saat_ozeti,
    gunluk_saat_istatistigi,
    haftalik_gunluk_randevu_sayisi,
    en_uygun_saatler,
)

# ✅ accounts/views.py dosyasına eklenmeli
from geopy.geocoders import Nominatim
from django.http import JsonResponse
from accounts.models import Profile
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def konum_al(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Giriş yapılmamış."}, status=403)

    try:
        data = json.loads(request.body)
        lat = data.get("latitude")
        lon = data.get("longitude")

        if not lat or not lon:
            return JsonResponse({"error": "Enlem veya boylam eksik."}, status=400)

        # 🌍 OpenStreetMap ile şehir bul
        geolocator = Nominatim(user_agent="kuafor_app")
        location = geolocator.reverse(f"{lat}, {lon}", language='tr')

        if location and 'address' in location.raw:
            address = location.raw['address']
            city = address.get('city') or address.get('town') or address.get('village')
        else:
            city = "Bilinmiyor"

        # 👤 Kullanıcı profilini güncelle
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.city = city
        profile.latitude = lat
        profile.longitude = lon
        profile.save()

        return JsonResponse({
            "success": True,
            "city": city,
            "latitude": lat,
            "longitude": lon
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# views.py
from django.shortcuts import render, redirect
from .forms import SalonMediaForm
from .models import SalonMedia

def upload_media(request):
    if request.method == 'POST':
        form = SalonMediaForm(request.POST, request.FILES)
        if form.is_valid():
            # Yüklenen medya dosyalarını alıyoruz
            media_files = request.FILES.getlist('media_file')
            for media in media_files:
                SalonMedia.objects.create(media_file=media)  # Medya dosyasını kaydediyoruz
            return redirect('success_url')  # Başarı sonrası yönlendirme
    else:
        form = SalonMediaForm()

    return render(request, 'upload_media.html', {'form': form})

from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

def link_callback(uri, rel):
    """
    xhtml2pdf, /static/... URI'lerini gerçek dosya yoluna çevirmek için bu
    fonksiyonu çağırır. Statik klasör dışındaki adresleri olduğu gibi döndürür.
    """
    if uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ''))
        if path:
            return path
    elif uri.startswith(settings.MEDIA_URL):
        return os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))

    # Diğer durumlarda olduğu gibi döndür (örneğin harici URL)
    return uri
   
def render_to_pdf_xhtml2pdf(template_path: str, context: dict | None = None) -> HttpResponse:
    context = context or {}

    # Font dosyasını tanımla
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
    if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    # HTML oluştur
    html_string = get_template(template_path).render(context)
    result = BytesIO()

    # PDF yaz
    pdf = pisa.pisaDocument(
        src=BytesIO(html_string.encode('utf-8')),
        dest=result,
        encoding='utf-8',
        link_callback=link_callback
    )

    if pdf.err:
        return HttpResponse("PDF oluşturulamadı", status=500)

    return HttpResponse(
        result.getvalue(),
        content_type='application/pdf',
        headers={'Content-Disposition': 'inline; filename="randevu.pdf"'}
    )

# ------------------------------------------------------------------
# Tek randevu PDF view’i (xhtml2pdf)
# ------------------------------------------------------------------

# Font dosyasını kaydet
# xhtml2pdf için
@login_required
def randevu_pdf_xhtml2pdf(request, id):
    """
    /appointments/<id>/pdf/  →  randevuyu PDF olarak döndürür.
    """
    appt = get_object_or_404(Appointment, id=id, user=request.user)
    context = {'appointment': appt}
    return render_to_pdf_xhtml2pdf('appointments/randevu_pdf.html', context)

# Font dosyasını kaydet

# PDF yardımcıları
# ------------------------------------------------------------------
def link_callback(uri, rel):
    """xhtml2pdf'in /static/... URI'lerini gerçek dosya yoluna çevirir."""
    if uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ''))
        if path:
            return path
    raise FileNotFoundError(f"Statik dosya bulunamadı: {uri}")

def render_to_pdf(template_path, context_dict=None):
    context_dict = context_dict or {}

    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')

    if not os.path.exists(font_path):
        return HttpResponse("DejaVuSans.ttf dosyası bulunamadı.", status=500)

    if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    template = get_template(template_path)
    html = template.render(context_dict)
    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(html.encode("utf-8")),
        result,
        encoding='utf-8',
        link_callback=link_callback
    )

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("PDF oluşturulamadı", status=500)

# ------------------------------------------------------------------
# Kullanıcı giriş/kayıt
# ------------------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_invalid(self, form):
        messages.error(self.request, _('❌ Kullanıcı adı veya parola hatalı.'))
        return super().form_invalid(form)

# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomRegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Parola", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Parola (Tekrar)", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError("Parolalar eşleşmiyor.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
# ------------------------------------------------------------------
# Anasayfa & takvim
# ------------------------------------------------------------------
from django.utils.timezone import localdate, make_aware
from datetime import datetime, time, timedelta
from .models import Appointment
from .utils import (
    tahmini_saat_ozeti,
    gunluk_saat_istatistigi,
    en_yogun_saat_araligi,
    haftalik_gunluk_randevu_sayisi,
    bu_ay_en_sik_saat
)

# appointments/views.py
# views.py
from django.shortcuts import render

from django.utils.timezone import localdate, make_aware
from datetime import datetime, timedelta, time
from .models import Appointment, Salon, SalonMedia

from .utils import (
    tahmini_saat_ozeti,
    gunluk_saat_istatistigi,
    en_yogun_saat_araligi,
    tahmin_motoru,
    toplu_pdf_olustur,
    gunluk_grafik_base64,
    en_bos_saat
)

from django.shortcuts import render

from django.utils.timezone import make_aware, localdate
from datetime import datetime, timedelta
from .models import Appointment, Salon, SalonMedia
from .utils import (
    tahmini_saat_ozeti,
    gunluk_saat_istatistigi,
    en_yogun_saat_araligi,
    tahmin_motoru
)

@login_required
def home_view(request):
    user = request.user
    today = localdate()
    start = make_aware(datetime.combine(today, datetime.min.time()))
    end = make_aware(datetime.combine(today, datetime.max.time()))

    salon = Salon.objects.filter(user=user).first()

    randevu_sayisi = Appointment.objects.filter(appointment_date__range=(start, end), salon=salon).count()
    haftalik = Appointment.objects.filter(appointment_date__date__gte=today - timedelta(days=6), salon=salon).count()
    aylik = Appointment.objects.filter(appointment_date__month=today.month, salon=salon).count()
   
    önerilen_saat = tahmini_saat_ozeti(user)
    gunluk_oneri = gunluk_saat_istatistigi(user)
    en_yogun_saat = en_yogun_saat_araligi(user)
    tahmin = tahmin_motoru(user)
    son_randevu = Appointment.objects.filter(user=user).order_by('-appointment_date').first()

    posts = (
        ReelPost.objects
        .filter(salon__user=user)
         .exclude(id__isnull=True)
        .prefetch_related('media')  # 👈 HATA BURADA DEĞİL, DOĞRU
        .order_by('-created_at')[:10]
    )

    secilen_tarih = request.GET.get('tarih')
    secilen_randevular = []
    grafik_base64 = None
    en_uygun_saat = None
    zaman = request.GET.get("zaman")

    if zaman == "bugun":
        secilen_randevular = Appointment.objects.filter(salon=salon, appointment_date__date=today)
        secilen_tarih = today
    elif zaman == "hafta":
        secilen_randevular = Appointment.objects.filter(salon=salon, appointment_date__date__gte=today - timedelta(days=6))
        secilen_tarih = f"{(today - timedelta(days=6)).strftime('%d.%m')} - {today.strftime('%d.%m')}"
    elif zaman == "ay":
        secilen_randevular = Appointment.objects.filter(salon=salon, appointment_date__month=today.month)
        secilen_tarih = f"{today.strftime('%B %Y')}"

    if salon and secilen_tarih:
        try:
            tarih = datetime.strptime(str(secilen_tarih), '%Y-%m-%d').date()
            secilen_start = make_aware(datetime.combine(tarih, time(0, 0)))
            secilen_end = make_aware(datetime.combine(tarih, time(23, 59)))
            secilen_randevular = Appointment.objects.filter(salon=salon, appointment_date__range=(secilen_start, secilen_end))
            grafik_base64 = gunluk_grafik_base64(secilen_randevular)
            en_uygun_saat = en_bos_saat(secilen_randevular, tarih)
        except ValueError:
            pass

    return render(request, "appointments/home.html", {
        "randevu_sayisi": randevu_sayisi,
        "haftalik": haftalik,
        "aylik": aylik,
        "önerilen_saat": önerilen_saat,
        "gunluk_oneri": gunluk_oneri,
        "en_yogun_saat": en_yogun_saat,
        "tahmin": tahmin,
        "son_randevu": son_randevu,
        "posts": posts,
        "reels": posts,
        "secilen_randevular": secilen_randevular,
        "secilen_tarih": secilen_tarih,
        "grafik_base64": grafik_base64,
        "en_uygun_saat": en_uygun_saat,
    })

@login_required
def gunluk_pdf_view(request):
    user = request.user
    salon = Salon.objects.filter(user=user).first()
    tarih_str = request.GET.get("tarih")

    if not salon or not tarih_str:
        return HttpResponse("Geçersiz istek", status=400)

    try:
        tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()
        start = make_aware(datetime.combine(tarih, time(0, 0)))
        end = make_aware(datetime.combine(tarih, time(23, 59)))
    except ValueError:
        return HttpResponse("Tarih biçimi geçersiz", status=400)

    randevular = Appointment.objects.filter(salon=salon, appointment_date__range=(start, end))

    html_string = render_to_string("appointments/pdf_gunluk.html", {
        "randevular": randevular,
        "tarih": tarih
    })

    html = HTML(string=html_string)
    result = tempfile.NamedTemporaryFile(delete=True, suffix=".pdf")
    html.write_pdf(result.name)

    with open(result.name, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="randevular_{tarih}.pdf"'
        return response
    
from django.contrib import messages

from appointments.forms import AppointmentForm
from appointments.models import Salon

from appointments.utils import tahmini_saat_ozeti

@login_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user

            # Kullanıcıya ait ilk salonu al
            salon = Salon.objects.filter(user=request.user).first()
            if not salon:
                messages.error(request, "Salon bilgisi bulunamadı. Lütfen önce bir salon oluşturun.")
                return redirect('appointments:appointment_list')

            appointment.salon = salon

            # Çakışma kontrolü
            existing = appointment.__class__.objects.filter(
                appointment_date=appointment.appointment_date,
                appointment_time=appointment.appointment_time,
                salon=appointment.salon
            ).exists()
            if existing:
                messages.error(request, "Bu saatte zaten bir randevu var.")
                return redirect('appointments:create_appointment')

            appointment.save()
            messages.success(request, "Randevunuz başarıyla oluşturuldu.")
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentForm(initial={'appointment_date': tahmini_saat_ozeti(request.user)}, user=request.user)

    return render(request, 'appointments/create_appointment.html', {
        'form': form,
        'tahmini_saat': tahmini_saat_ozeti(request.user),
    })

from django.contrib import messages
from django.shortcuts import render, redirect
from appointments.models import Appointment, Salon
from django.utils.timezone import make_aware, localdate
from datetime import datetime, time


@login_required
def appointment_list(request):
    user = request.user

    # Kullanıcının salonunu al
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        messages.error(request, "Salon bulunamadı. Lütfen önce salon bilgilerinizi oluşturun.")
        return redirect('accounts:profile')  # ❗ BU satır if'in içinde olmalı

    # Bugünün tarih aralığını al
    today = localdate()
    start = make_aware(datetime.combine(today, time.min))
    end = make_aware(datetime.combine(today, time.max))

    # Bugünkü randevular
    appointments = Appointment.objects.filter(
        salon=salon,
        appointment_date__range=(start, end)
    )

    # Geçmiş randevular
    past_appointments = Appointment.objects.filter(
        salon=salon,
        appointment_date__lt=start
    )

    # Arama sorgusu
    q = request.GET.get('q')
    if q:
        appointments = appointments.filter(customer_name__icontains=q)

    context = {
        'appointments': appointments,
        'past_appointments': past_appointments,
        'q': q,
    }
    return render(request, 'appointments/appointment_list.html', context)


@csrf_protect
@login_required
def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id, user=request.user)


    if request.method == 'POST':
        appointment.delete()
        return redirect('appointments:appointment_list')

    return render(request, 'appointments/delete_appointment.html', {
        'appointment': appointment
    })


@login_required
def whatsapp_yonlendir(request, id):
    """
    Randevu bilgisiyle WhatsApp mesaj linkine yönlendirir.
    """
    appt = get_object_or_404(Appointment, id=id, user=request.user)

    text = _('Merhaba {name}, {date} tarihinde kuaför randevunuz oluşturuldu.').format(
        name=appt.customer_name,
        date=appt.appointment_date.strftime('%d.%m.%Y %H:%M')
    )
    # Boşlukları %20 ile kodla → basit URL-encode
    url = f"https://wa.me/{appt.phone_number}?text={text.replace(' ', '%20')}"
    return redirect(url)

# ------------------------------------------------------------------
# Randevu başarı sayfası
# ------------------------------------------------------------------
@login_required
def randevu_basarili(request, id):
    """
    Randevu kaydı sonrasında “Başarılı” ekranını gösterir.
    """
    appt = get_object_or_404(Appointment, id=id, user=request.user)
    return render(request, 'appointments/randevu_basarili.html', {'appointment': appt})

@login_required
def randevu_pdf(request, id):
    appointment = get_object_or_404(Appointment, id=id, user=request.user)
    return render_to_pdf('appointments/randevu_pdf.html', {'appointment': appointment})

from appointments.models import Salon

@login_required
def zip_randevu_pdfs(request):
    """
    Kullanıcının salonuna ait tüm randevuları PDF olarak üretir ve ZIP dosyası olarak indirir.
    """
    kullanici_salon = Salon.objects.get(user=request.user)
    appts = Appointment.objects.filter(salon=kullanici_salon).order_by('-appointment_date')

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for appt in appts:
            pdf = render_to_pdf('appointments/randevu_pdf.html', {'appointment': appt})
            zf.writestr(f"randevu_{appt.id}.pdf", pdf.content)
    
    buf.seek(0)
    return HttpResponse(buf.getvalue(),
                        content_type='application/zip',
                        headers={'Content-Disposition': 'attachment; filename="tum_randevular.zip"'})
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from .models import Salon, Appointment

@login_required
def grafik_pdf_view(request):
    salon = Salon.objects.filter(user=request.user).first()

    # Ay filtresi al
    ay_str = request.GET.get('ay')
    if ay_str:
        try:
            selected_date = datetime.strptime(ay_str, '%Y-%m').date()
        except ValueError:
            selected_date = now().date()
    else:
        selected_date = now().date()

    # Aylık veri hesapla
    aylik_baslangic = selected_date.replace(day=1)
    next_month = (aylik_baslangic.replace(day=28) + timedelta(days=4)).replace(day=1)
    gun_sayisi = (next_month - timedelta(days=1)).day

    aylik_gunler = []
    aylik_sayilar = []

    for i in range(1, gun_sayisi + 1):
        gun = aylik_baslangic.replace(day=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        sayi = Appointment.objects.filter(
            appointment_date__range=(start, end),
            salon=salon
        ).count()
        aylik_gunler.append(gun.strftime('%d.%m.%Y'))
        aylik_sayilar.append(sayi)

    html_string = render_to_string('appointments/grafik_pdf.html', {
        'salon': salon,
        'tarih': selected_date,
        'veriler': zip(aylik_gunler, aylik_sayilar),
    })

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="randevu_raporu_{selected_date.strftime("%Y-%m")}.pdf"'
    return response

from matplotlib import pyplot as plt
from io import BytesIO
from django.http import HttpResponse
from django.db.models.functions import ExtractHour
from django.db.models import Count

from .models import Appointment

from appointments.models import Salon


from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import json

from django.utils.dateparse import parse_date

@login_required
def randevu_grafik_view(request):
    salon = Salon.objects.filter(user=request.user).first()


    # 🔽 Ay bilgisi URL parametresinden alınır, yoksa bugünkü ay
    ay_str = request.GET.get('ay')
    if ay_str:
        try:
            selected_date = datetime.strptime(ay_str, '%Y-%m').date()
        except ValueError:
            selected_date = now().date()
    else:
        selected_date = now().date()

    today = now().date()

    # Günlük + haftalık veriler aynı kalır
    start_today = make_aware(datetime.combine(today, datetime.min.time()))
    end_today = make_aware(datetime.combine(today, datetime.max.time()))
    bugun_sayisi = Appointment.objects.filter(
        appointment_date__range=(start_today, end_today),
        salon=salon
    ).count()

    haftalik_baslangic = today - timedelta(days=6)
    haftalik_data = []
    gunler = []

    for i in range(7):
        gun = haftalik_baslangic + timedelta(days=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        sayi = Appointment.objects.filter(
            appointment_date__range=(start, end),
            salon=salon
        ).count()
        haftalik_data.append(sayi)
        gunler.append(gun.strftime('%d.%m'))

    # 📆 Aylık analiz filtreli
    aylik_baslangic = selected_date.replace(day=1)
    next_month = (aylik_baslangic.replace(day=28) + timedelta(days=4)).replace(day=1)
    gun_sayisi = (next_month - timedelta(days=1)).day

    aylik_gunler = []
    aylik_sayilar = []

    for i in range(1, gun_sayisi + 1):
        gun = aylik_baslangic.replace(day=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        sayi = Appointment.objects.filter(
            appointment_date__range=(start, end),
            salon=salon
        ).count()
        aylik_gunler.append(gun.strftime('%d'))
        aylik_sayilar.append(sayi)

    # Haftalık grafik
    plt.figure(figsize=(8, 4))
    plt.bar(gunler, haftalik_data, color='skyblue')
    plt.title(f"{salon.name} için Son 7 Günlük Randevu Sayısı")
    plt.xlabel("Tarih")
    plt.ylabel("Randevu Sayısı")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    return render(request, 'appointments/randevu_grafik.html', {
        'bugun_sayisi': bugun_sayisi,
        'grafik': image_base64,
        'aylik_gunler': json.dumps(aylik_gunler),
        'aylik_sayilar': json.dumps(aylik_sayilar),
        'secili_ay': selected_date.strftime('%Y-%m')
    })


from appointments.models import Salon

@login_required
def graph_data(request):
    salon = get_object_or_404(Salon, user=request.user)
    raw = haftalik_gunluk_randevu_sayisi(request.user, salon=salon)
    data = [{'gun': r['gun'].strftime('%a'), 'adet': r['adet']} for r in raw]
    return JsonResponse(data, safe=False)

# ------------------------------------------------------------------
# Yapay Zeka Saat Paneli
# ------------------------------------------------------------------
from django.utils.timezone import make_aware, now
from datetime import datetime, time
from django.shortcuts import render, get_object_or_404
from .models import Appointment
from .utils import en_uygun_saatler
from django.utils import timezone

from appointments.models import Salon

@login_required
def saat_durumu_paneli(request):
    salon = Salon.objects.filter(user=request.user).first()

    tarih_str = request.GET.get('tarih')
    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else now().date()
    except ValueError:
        tarih = now().date()

    gun_baslangic = make_aware(datetime.combine(tarih, time(9, 0)))
    gun_bitis     = make_aware(datetime.combine(tarih, time(19, 59)))

    randevular = (
        Appointment.objects
        .filter(salon=salon, appointment_date__range=(gun_baslangic, gun_bitis))
        .values_list('appointment_date', flat=True)
    )

    dolu_saatler = {
        dt.astimezone(timezone.get_current_timezone()).strftime('%H:00')
        for dt in randevular
    }

    saat_listesi = [f"{h:02d}:00" for h in range(9, 20)]
    durumlar     = [(saat, saat in dolu_saatler) for saat in saat_listesi]

    uygun_saatler = en_uygun_saatler(tarih, request.user, salon=salon)

    return render(request, 'appointments/saat_durumu.html', {
        'tarih'        : tarih,
        'durumlar'     : durumlar,
        'uygun_saatler': uygun_saatler,
    })

@login_required
def en_uygun_saat_api(request):
    salon = Salon.objects.filter(user=request.user).first()


    tarih_str = request.GET.get('tarih')
    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else now().date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Tarih formatı geçersiz. Örnek: 2025-05-04'}, status=400)

    saatler = list(en_uygun_saatler(tarih, request.user, salon=salon))
    return JsonResponse({'saatler': saatler})

def en_uygun_saatler(tarih, user, salon=None):
    saat_listesi = [f"{s:02d}:00" for s in range(9, 20)]
    uygunlar = []

    for saat_str in saat_listesi:
        saat_obj = make_aware(datetime.combine(tarih, datetime.strptime(saat_str, "%H:%M").time()))
        qs = Appointment.objects.filter(appointment_date=saat_obj, user=user)
        if salon:
            qs = qs.filter(salon=salon)
        if not qs.exists():
            uygunlar.append(saat_str)

    return uygunlar[:3]

# ------------------------------------------------------------------
# Test verisi
# ------------------------------------------------------------------
from django.shortcuts import redirect
from .models import Appointment
from django.utils.timezone import now
import random
from datetime import timedelta


@login_required
def test_randevu_ekle(request):
    """
    Test amaçlı 5 sahte randevu oluşturur.
    """
    salons = ['Salon A', 'Salon B']
    base_date = now()

    for i in range(5):
        Appointment.objects.create(
            user=request.user,
            customer_name=f'Test Kullanıcı {i + 1}',
            phone_number=f'555000000{i}',
            salon_name=random.choice(salons),
            appointment_date=base_date + timedelta(days=i)
        )

    return redirect('appointments:appointment_list')


from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from django.shortcuts import get_object_or_404, render

from .models import Appointment  # Bu satır eksikse eklenmeli
@login_required
def randevu_pdf_weasy(request, id):
    appointment = get_object_or_404(Appointment, id=id, user=request.user)
    template = get_template('appointments/randevu_pdf.html')
    html_string = template.render({'appointment': appointment})

    # Font dosyasını bul
    font_path = finders.find("fonts/DejaVuSans.ttf")
    if not font_path:
        return HttpResponse("Font dosyası bulunamadı.", status=500)

    font_config = FontConfiguration()

    # CSS tanımı
    css = CSS(string=f"""
        @font-face {{
            font-family: 'DejaVuSans';
            src: url("file://{font_path}");
        }}
        body {{
            font-family: 'DejaVuSans', sans-serif;
            font-size: 14px;
            color: #222;
        }}
    """, font_config=font_config)

    # Bellekte PDF oluştur
    pdf_bytes = HTML(string=html_string).write_pdf(stylesheets=[css], font_config=font_config)

    return HttpResponse(pdf_bytes, content_type='application/pdf', headers={
        'Content-Disposition': f'inline; filename="randevu_{id}.pdf"'
    })

@login_required
@csrf_exempt
def calendar_events(request):
    salon = Salon.objects.get(user=request.user)
    appointments = Appointment.objects.filter(salon=salon)

    kategori_renkleri = {
        'kadın': '#e83e8c',
        'erkek': '#007bff',
        'cocuk': '#20c997'
    }

    events = []
    for a in appointments:
        color = kategori_renkleri.get(a.category, '#6c757d')  # varsayılan gri
        events.append({
            "id": a.id,
            "title": a.customer_name,
            "start": a.appointment_date.isoformat(),
            "color": color,
            "extendedProps": {
                "phone": a.phone_number,
                "kategori": a.get_category_display(),
                "tarih": a.appointment_date.strftime("%d.%m.%Y %H:%M")
            }
        })
    return JsonResponse(events, safe=False)

@login_required
def kullanici_paneli(request):
    user = request.user
    randevular = Appointment.objects.filter(user=user).order_by('-appointment_date')
    return render(request, 'appointments/kullanici_paneli.html', {
        'randevular': randevular
    })

# views.py içinde
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import base64
from io import BytesIO

@login_required
def takvim_pdf_view(request):
    salon = Salon.objects.get(user=request.user)
    today = now().date()

    # 1️⃣ Son 7 Günlük Detay Veriler
    detaylar = []
    toplam = 0
    en_yogun = ("", 0)
    for i in range(6, -1, -1):
        gun = today - timedelta(days=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        randevular = Appointment.objects.filter(appointment_date__range=(start, end), salon=salon)
        detaylar.append({
            "tarih": gun.strftime("%d.%m.%Y"),
            "musteriler": list(randevular.values_list("customer_name", flat=True))
        })
        if len(randevular) > en_yogun[1]:
            en_yogun = (gun.strftime("%A (%d.%m.%Y)"), len(randevular))
        toplam += len(randevular)

    # 2️⃣ Yapay Zeka Saat Tahmini
    from appointments.utils import tahmini_saat_ozeti
    tahmin = tahmini_saat_ozeti(request.user) or "Yeterli veri yok"

    # 3️⃣ QR Kodu Oluştur
    qr = qrcode.make(request.build_absolute_uri('/appointments/'))
    buf = BytesIO()
    qr.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    # 4️⃣ PDF HTML Render
    html = render_to_string("appointments/takvim_pdf.html", {
        "salon": salon,
        "detaylar": detaylar,
        "logo_url": request.build_absolute_uri('/static/logo.png'),
        "tarih": now().strftime("%d.%m.%Y %H:%M"),
        "toplam": toplam,
        "en_yogun_gun": en_yogun[0],
        "tahmin": tahmin,
        "qr_base64": qr_base64,
        "slogan": "Kendi Hikayeni Şekillendir ✂️"
    })

    # 5️⃣ Stil Ayarı + Font
    font_config = FontConfiguration()
    font_path = finders.find("fonts/DejaVuSans.ttf")
    css = CSS(string=f"""
        @page {{
            size: A4 landscape;
            margin: 2cm;
        }}
        @font-face {{
            font-family: 'DejaVuSans';
            src: url('file://{font_path}');
        }}
        body {{ font-family: 'DejaVuSans', sans-serif; }}
    """, font_config=font_config)

    pdf = HTML(string=html).write_pdf(stylesheets=[css], font_config=font_config)

    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=takvim.pdf"
    })

from django.http import JsonResponse


@login_required
def calendar_page(request):
    return render(request, 'appointments/calendar.html')

from django.shortcuts import get_object_or_404, render
from appointments.models import Appointment


@login_required
def appointment_detail(request, id):
    appointment = get_object_or_404(Appointment, id=id, user=request.user)
    return render(request, 'appointments/appointment_detail.html', {
        'appointment': appointment
    })

# accounts/views.py

from appointments.models import Salon

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Kullanıcı için otomatik salon oluştur
            Salon.objects.create(user=user, salon_name="Benim Salonum")

            login(request, user)
            messages.success(request, "Kayıt başarılı, hoş geldiniz!")
            return redirect('appointments:appointment_list')
    ...
# appointments/views.py
@login_required
def haftalik_grafik_view(request):
    return render(request, 'appointments/haftalik_grafik.html')

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from io import BytesIO
from django.contrib.staticfiles import finders
from appointments.models import Appointment, Salon

import base64

@login_required
def takvim_pdf_view(request):
    salon = Salon.objects.get(user=request.user)
    today = now().date()

    # 📊 Son 7 Günlük Veriler
    detaylar = []
    toplam = 0
    en_yogun = ("", 0)
    for i in range(6, -1, -1):
        gun = today - timedelta(days=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        randevular = Appointment.objects.filter(appointment_date__range=(start, end), salon=salon)
        detaylar.append({
            "tarih": gun.strftime("%d.%m.%Y"),
            "musteriler": list(randevular.values_list("customer_name", flat=True))
        })
        if len(randevular) > en_yogun[1]:
            en_yogun = (gun.strftime("%A (%d.%m.%Y)"), len(randevular))
        toplam += len(randevular)

    from appointments.utils import tahmini_saat_ozeti
    tahmin = tahmini_saat_ozeti(request.user) or "Yeterli veri yok"
    import qrcode
    import base64

    qr = qrcode.make(request.build_absolute_uri('/appointments/'))
    buf = BytesIO()
    qr.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    html = render_to_string("appointments/takvim_pdf.html", {
        "salon": salon,
        "detaylar": detaylar,
        "logo_url": request.build_absolute_uri('/static/logo.png'),
        "tarih": now().strftime("%d.%m.%Y %H:%M"),
        "toplam": toplam,
        "en_yogun_gun": en_yogun[0],
        "tahmin": tahmin,
        "slogan": "Kendi Hikâyeni Şekillendir ✂️"
    })

    font_config = FontConfiguration()
    font_path = finders.find("fonts/DejaVuSans.ttf")
    css = CSS(string=f"""
        @font-face {{
            font-family: 'DejaVuSans';
            src: url('file://{font_path}');
        }}
        @page {{
            size: A4 landscape;
            margin: 2cm;
        }}
        body {{
            font-family: 'DejaVuSans', sans-serif;
        }}
    """, font_config=font_config)

    pdf = HTML(string=html).write_pdf(stylesheets=[css], font_config=font_config, presentational_hints=True)

    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=takvim.pdf"
    })


from django.utils.timezone import make_aware, now
from django.shortcuts import render
from datetime import datetime, timedelta
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import json

from .models import Appointment, Salon

@login_required
def takvim_view(request):
    salon = Salon.objects.get(user=request.user)
    appointments = Appointment.objects.filter(salon=salon)

    # 🔹 Kategoriye göre renkler
    kategori_renk = {
        'kadın': '#0d6efd',   # Mavi
        'erkek': '#dc3545',   # Kırmızı
        'cocuk': '#ffc107',   # Sarı
    }

    # 🔹 Event listesi (takvim için)
    events = []
    for r in appointments:
        events.append({
            "id": r.id,
            "title": r.customer_name,
            "start": r.appointment_date.isoformat(),
            "category": r.category,
            "phone": r.phone_number,
            "tarih": r.appointment_date.strftime('%d.%m.%Y %H:%M'),
            "color": kategori_renk.get(r.category, '#6c757d')
        })

    # 🔹 Son 7 günlük yoğunluk verisi (grafik için)
    gunler = []
    sayilar = []
    for i in range(6, -1, -1):
        gun = datetime.today().date() - timedelta(days=i)
        start = make_aware(datetime.combine(gun, datetime.min.time()))
        end = make_aware(datetime.combine(gun, datetime.max.time()))
        adet = appointments.filter(appointment_date__range=(start, end)).count()
        gunler.append(gun.strftime('%d.%m'))
        sayilar.append(adet)

    plt.figure(figsize=(6, 3))
    plt.plot(gunler, sayilar, marker='o', color='#0d6efd')
    plt.fill_between(gunler, sayilar, alpha=0.2, color='#cce5ff')
    plt.title("📊 Son 7 Günlük Randevu Yoğunluğu")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    grafik_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return render(request, 'appointments/takvim.html', {
        'events': json.dumps(events),
        'grafik': grafik_base64
    })

# appointments/views.py


from .models import Salon, SalonMedia, ReelPost
from .forms import ReelUploadForm

@login_required
def upload_post(request):
    salon = get_object_or_404(Salon, user=request.user)

    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        files = request.FILES.getlist('media_files')
        post = ReelPost.objects.create(salon=salon, description=caption)

        for file in files:
            ext = file.name.split('.')[-1].lower()
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
            SalonMedia.objects.create(post=post, media_file=file, type=media_type)

        return redirect('appointments:reels_list')

    return render(request, 'salon/reels_upload.html')

@login_required
def media_gallery_view(request):
    salon = Salon.objects.get(user=request.user)
    media_list = SalonMedia.objects.filter(salon=salon).order_by('-created_at')
    return render(request, 'appointments/media_gallery.html', {'media_list': media_list})

# appointments/views.py
from accounts.models import FavoriteSalon

from .models import Salon, SalonComment
from .forms import SalonCommentForm
from django.shortcuts import get_object_or_404, redirect, render


# views.py

from django.shortcuts import render, redirect

from .models import SalonMedia, Salon

@login_required
def reels_upload(request):
    if request.method == 'POST':
        form = SalonMediaForm(request.POST, request.FILES)
        if form.is_valid():
            reel = form.save(commit=False)
            reel.salon = Salon.objects.get(user=request.user)
            reel.type = 'video' if 'video' in reel.media_file.name.lower() else 'image'
            reel.save()
            return redirect('appointments:reels_list')
    else:
        form = SalonMediaForm()
    return render(request, 'salon/reels_upload.html', {'form': form})

from django.shortcuts import render

from .models import ReelPost

@login_required
def reels_list(request):
    posts = (
        ReelPost.objects
        .select_related('salon')
        .prefetch_related('media')  # eğer media ilişkisi ManyToMany değilse 'salonmedia_set'
        .order_by('-created_at')
    )
    return render(request, 'salon/reels_list.html', {'posts': posts})

from .models import AnlikPaylasim
from django.utils import timezone
from datetime import timedelta

@login_required
def anlik_list(request):
    now = timezone.now()
    paylasimlar = AnlikPaylasim.objects.filter(
        salon__user=request.user,
        created_at__gte=now - timedelta(hours=24)
    ).order_by('-created_at')

    return render(request, 'salon/anlik_list.html', {'paylasimlar': paylasimlar})
from django.http import HttpResponse

from django.shortcuts import render, redirect
from .models import Salon, AnlikPaylasim

@login_required
def upload_anlik(request):
    if request.method == 'POST':
        files = request.FILES.getlist('media_files')
        salon = Salon.objects.filter(user=request.user).first()


        for file in files:
            ext = file.name.split('.')[-1].lower()
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
            AnlikPaylasim.objects.create(salon=salon, media_file=file, type=media_type)

        return redirect('appointments:anlik_list')

    # Bu satır sadece POST değilse çalışmalı
    return render(request, 'salon/upload_anlik.html')

from .utils import yapay_zeka_muzik_sec

def upload_post(request):
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        files = request.FILES.getlist('media_files')
        salon = Salon.objects.filter(user=request.user).first()


        post = SalonPost.objects.create(salon=salon, description=caption)

        for file in files:
            ext = file.name.split('.')[-1].lower()
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
            SalonMedia.objects.create(post=post, media_file=file, type=media_type)

        # 🎵 Yapay zekâ ile otomatik müzik ekle
        post.muzik = yapay_zeka_muzik_sec()
        post.save()

        return redirect('appointments:reels_list')

    return render(request, 'salon/upload_post.html')

from django.http import HttpResponse


@login_required
def upload_media_view(request):
    return HttpResponse("Medya yükleme sayfası başarıyla çalışıyor.")

from django.utils.timezone import now

from django.shortcuts import redirect

# appointments/views.py


from django.shortcuts import redirect
from appointments.models import Appointment, Salon
from django.contrib.auth.models import User
from django.utils.timezone import now

@login_required
def test_randevu_ekle(request):
    user = request.user
    salon = Salon.objects.filter(user=user).first()

    for i in range(3):
        Appointment.objects.create(
            customer_name=f"Deneme Müşteri {i}",
            phone_number=f"55500000{i}",
            appointment_date=now(),
            user=user,
            salon=salon
        )

    return redirect("appointments:appointment_list")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
from datetime import datetime, timedelta

def generate_weekly_chart():
    today = datetime.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    counts = [random.randint(1, 10) for _ in days]

    plt.figure(figsize=(8, 4))
    plt.plot(days, counts, marker='o', linestyle='-', linewidth=2)
    plt.title("Haftalık Randevu Dağılımı")
    plt.xlabel("Tarih")
    plt.ylabel("Randevu Sayısı")
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    return image_base64

from django.db.models import Avg
from appointments.models import Appointment, SalonComment
from appointments.models import Salon
from appointments.utils import randevu_aylik_grafik_base64

@login_required
def kullanici_paneli(request):
    user = request.user

    # 1. En sık tercih edilen saat
    saatler = Appointment.objects.filter(user=user).values_list('appointment_date__hour', flat=True)
    if saatler:
        en_sik_saat = max(set(saatler), key=saatler.count)
        en_sik_saat = f"{en_sik_saat:02d}:00"
    else:
        en_sik_saat = "Henüz yok"

    # 2. Favori salon (kullanıcı en çok hangi salona randevu almış)
    salon_sayilari = Appointment.objects.filter(user=user).values('salon_name').annotate(sayi=Count('id')).order_by('-sayi')
    favori_salon = salon_sayilari[0]['salon_name'] if salon_sayilari else "Henüz yok"

    # 3. Ortalama puan (yorumlardan)
    ortalama = SalonComment.objects.filter(user=user).aggregate(ortalama=Avg('puan'))['ortalama']
    ortalama_puan = round(ortalama, 1) if ortalama else "Henüz yok"

    # 4. Aylık grafik
    aylik_grafik = randevu_aylik_grafik_base64(user)

    return render(request, 'accounts/kullanici_paneli.html', {
        'en_sik_saat': en_sik_saat,
        'favori_salon': favori_salon,
        'ortalama_puan': ortalama_puan,
        'aylik_grafik': aylik_grafik,
    })

from .models import Salon, SalonComment

    
# appointments/views.py
from django.shortcuts import render

from django.db.models import Avg, Count
from .models import Appointment, SalonComment
from .utils import randevu_aylik_grafik_base64, tahmini_saat_ozeti


@login_required
def kullanici_paneli(request):
    user = request.user

    # 1️⃣ Ortalama puan hesapla
    ortalama_puan = SalonComment.objects.filter(user=user, approved=True).aggregate(Avg('puan'))['puan__avg']
    ortalama_puan = round(ortalama_puan, 1) if ortalama_puan else "Henüz yok"

    # 2️⃣ Favori salonu bul (en çok yorum yaptığı)
    favori = (
        SalonComment.objects.filter(user=user, approved=True)
        .values('salon__name')
        .annotate(toplam=Count('id'))
        .order_by('-toplam')
        .first()
    )
    favori_salon = favori['salon__name'] if favori else "Henüz yorum yapılmadı"

    # 3️⃣ En çok tercih edilen saat
    en_sik_saat = tahmini_saat_ozeti(user)

    # 4️⃣ Aylık randevu grafiği (base64)
    aylik_grafik = randevu_aylik_grafik_base64(user)

    return render(request, 'appointments/kullanici_paneli.html', {
        'ortalama_puan': ortalama_puan,
        'favori_salon': favori_salon,
        'en_sik_saat': en_sik_saat,
        'aylik_grafik': aylik_grafik,
    })

from appointments.utils import randevu_aylik_grafik_base64

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect

@csrf_protect  # CSRF koruması aktif
def toggle_theme(request):
    # Geldiği sayfaya geri yönlendir
    response = redirect(request.META.get('HTTP_REFERER', '/'))

    # Mevcut tema çerezini al ('light' varsayılan)
    current = request.COOKIES.get('theme', 'light')

    # Yeni değeri belirle: light ise dark yap, değilse light yap
    new_theme = 'dark' if current == 'light' else 'light'

    # Yeni değeri çerez olarak ayarla
    response.set_cookie('theme', new_theme)

    return response

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views import View

CustomUser = get_user_model()

class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        username = request.POST.get('username')

        # 🔒 Kullanıcı daha önce kayıt oldu mu kontrolü
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request, _('⚠️ Bu kullanıcı adıyla zaten kayıt yapılmış. Lütfen giriş yapın.'))
            return redirect('accounts:login')

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('✅ Kayıt başarılı! Hoş geldiniz.'))
            return redirect('appointments:appointment_list')
        else:
            messages.error(request, _('❌ Kayıt başarısız. Lütfen formu kontrol edin.'))

        # Form geçerli ya da geçersiz olsa da aynı sayfaya geri döneceğiz
        return render(request, 'accounts/register.html', {'form': form})

from django.shortcuts import get_object_or_404, redirect

from .models import SalonMedia
from .models import ReelLike  # Eğer bu modelin varsa

from django.shortcuts import get_object_or_404, redirect

from .models import SalonMedia
from .models import ReelLike  # Eğer bu modelin varsa

@login_required
def reel_begen(request, id):
    media = get_object_or_404(SalonMedia, id=id)
    user = request.user

    # Aynı kullanıcı daha önce beğendiyse tekrar eklenmez
    if not media.reellike_set.filter(user=user).exists():
        media.reellike_set.create(user=user)

    return redirect('appointments:reels_list')

@login_required
def reel_yorum(request, id):
    # Yorum formuna yönlendir
    return redirect('appointments:home')

from django.shortcuts import get_object_or_404, redirect, render
from .forms import ReelCommentForm
from .models import ReelComment, SalonMedia

@login_required
def reel_yorum(request, id):
    media = get_object_or_404(SalonMedia, id=id)

    if request.method == 'POST':
        form = ReelCommentForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.media = media
            yorum.user = request.user
            yorum.save()
            return redirect('appointments:reels_list')
    else:
        form = ReelCommentForm()

    return render(request, 'appointments/reel_yorum_form.html', {
        'form': form,
        'media': media
    })

@login_required
def reel_begen(request, reel_id):
    reel = get_object_or_404(ReelPost, id=reel_id)
    like, created = ReelLike.objects.get_or_create(user=request.user, reel=reel)
    if not created:
        like.delete()
    return redirect('appointments:reels_list')


@login_required
def reel_yorum(request, reel_id):
    reel = get_object_or_404(ReelPost, id=reel_id)
    if request.method == "POST":
        form = ReelCommentForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.user = request.user
            yorum.reel = reel
            yorum.save()
    return redirect('appointments:reels_list')

from django.utils.timezone import make_aware
from datetime import datetime, time
from .models import Appointment

# views.py
from django.http import HttpResponse
from .utils import zip_randevular_pdf, gunluk_grafik_png, en_bos_saat
from django.utils.timezone import make_aware
from datetime import datetime, time

from django.http import HttpResponse
from django.utils.timezone import make_aware
from datetime import datetime, time

from .models import Appointment, Salon
from .utils import zip_randevular_pdf  # varsa dış fonksiyon

@login_required
def secilen_tarih_pdf_zip(request):
    tarih_str = request.GET.get("tarih")
    user = request.user

    # Kullanıcının salonu kontrolü
    salon = Salon.objects.filter(user=user).first()
    if not tarih_str or not salon:
        return HttpResponse("Tarih veya salon bulunamadı.", status=400)

    # Tarihi datetime'a çevirme
    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Geçersiz tarih formatı", status=400)

    # Başlangıç ve bitiş saatlerini ayarla (günlük aralık)
    start = make_aware(datetime.combine(tarih, time(0, 0)))
    end = make_aware(datetime.combine(tarih, time(23, 59)))

    # Randevuları al ve ziple
    queryset = Appointment.objects.filter(salon=salon, appointment_date__range=(start, end))
    zip_bytes = zip_randevular_pdf(queryset)

    # Response dön
    response = HttpResponse(zip_bytes, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Randevular_{tarih_str}.zip"'
    return response

# views.py
from django.http import HttpResponse
from .utils import zip_randevular_pdf, gunluk_grafik_png, en_bos_saat
from django.utils.timezone import make_aware
from datetime import datetime, time


# views.py
from django.http import HttpResponse
from .utils import zip_randevular_pdf, gunluk_grafik_png, en_bos_saat
from django.utils.timezone import make_aware
from datetime import datetime, time



@login_required
def secilen_tarih_grafik_indir(request):
    tarih_str = request.GET.get("tarih")
    user = request.user
    salon = Salon.objects.filter(user=user).first()

    if not tarih_str or not salon:
        return HttpResponse("Tarih veya salon eksik.", status=400)

    tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
    start = make_aware(datetime.combine(tarih, time(0, 0)))
    end = make_aware(datetime.combine(tarih, time(23, 59)))

    randevular = Appointment.objects.filter(salon=salon, appointment_date__range=(start, end))
    grafik_bytes = gunluk_grafik_png(randevular)
    response = HttpResponse(grafik_bytes, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="Grafik_{tarih_str}.png"'
    return response

@login_required
def secilen_tarih_ai_json(request):
    tarih_str = request.GET.get("tarih")
    salon = Salon.objects.filter(user=request.user).first()

    if not tarih_str or not salon:
        return JsonResponse({'error': 'Eksik bilgi'}, status=400)

    tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
    start = make_aware(datetime.combine(tarih, time(0, 0)))
    end = make_aware(datetime.combine(tarih, time(23, 59)))
    queryset = Appointment.objects.filter(salon=salon, appointment_date__range=(start, end))

    saat = en_bos_saat(queryset, tarih)
    return JsonResponse({'en_uygun': saat or "Yok"})

@login_required
def zip_randevu_pdfs(request):
    randevular = Appointment.objects.filter(user=request.user)
    zip_bytes = zip_randevular_pdf(randevular)
    response = HttpResponse(zip_bytes, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="randevular.zip"'
    return response

from django.contrib.admin.views.decorators import staff_member_required
from .models import Appointment
from .utils import zip_randevular_pdf

@staff_member_required
def zip_randevular_view(request):
    queryset = Appointment.objects.all()
    zip_data = zip_randevular_pdf(queryset)
    response = HttpResponse(zip_data, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="tum_randevular.zip"'
    return response

from .models import Salon
from accounts.models import FavoriteSalon  # Eğer favori kontrolü varsa


@login_required
def salon_list(request):
    salonlar = Salon.objects.all()
    favori_listesi = list(
        FavoriteSalon.objects.filter(user=request.user).values_list('salon_id', flat=True)
    )
    return render(request, 'salon/salon_list.html', {
        'salonlar': salonlar,
        'favori_listesi': favori_listesi,
    })

from django.shortcuts import render, get_object_or_404
from .models import Salon, SalonComment, SalonMedia

def salon_detail(request, id):
    salon = get_object_or_404(Salon, id=id)
    yorumlar = SalonComment.objects.filter(salon=salon, approved=True)
    media_list = SalonMedia.objects.filter(post__salon=salon).order_by('-created_at')

    return render(request, 'salon/salon_detail.html', {
        'salon': salon,
        'yorumlar': yorumlar,
        'media_list': media_list,
    })


from django.db.models import Count
from .models import ReelPost
from django.shortcuts import render
from django.db.models import Count
from .models import ReelPost
from django.db.models import Count
from django.db.models import Count

from .models import ReelPost, SalonMedia
from django.db.models import Count

from django.shortcuts import render
from appointments.models import ReelPost  # __init__.py sayesinde direkt alınır

@login_required
def featured_reels_view(request):
    reels = ReelPost.objects.prefetch_related('media').order_by('-created_at')[:10]

    return render(request, 'appointments/featured_reels.html', {'reels': reels})

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def konum_al(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')

        # 3. Google Maps Geocoding API veya OpenStreetMap kullanılabilir
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=10"
        response = requests.get(url)
        city = "Bilinmiyor"

        if response.status_code == 200:
            jdata = response.json()
            city = jdata.get("address", {}).get("city", "Bilinmiyor")

        # Session veya User’a kaydet
        request.session['user_city'] = city
        return JsonResponse({'status': 'ok', 'city': city})

import pandas as pd
from django.utils.timezone import localtime
from .models import Appointment, Salon





def tahmin_motoru(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return None

    randevular = Appointment.objects.filter(salon=salon)
    if not randevular.exists():
        return None

    data = []
    for r in randevular:
        local_dt = localtime(r.appointment_date)
        data.append({
            'day': local_dt.strftime('%A'),
            'hour': local_dt.hour
        })

    df = pd.DataFrame(data)
    if df.empty:
        return None

    day_hour_stats = (
        df.groupby(['day', 'hour'])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    best_day = day_hour_stats.iloc[0]['day']
    best_hour = int(day_hour_stats.iloc[0]['hour'])

    return {
        "gun": best_day,
        "saat": f"{best_hour:02d}:00"
    }

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from geopy.geocoders import Nominatim
from accounts.models import Profile
import json

@csrf_exempt
def konum_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lat = data.get("latitude")
            lng = data.get("longitude")

            if not lat or not lng:
                return JsonResponse({"error": "Geçersiz koordinatlar."}, status=400)

            geolocator = Nominatim(user_agent="kuafor_app")
            location = geolocator.reverse(f"{lat}, {lng}", language='tr')

            if location and 'address' in location.raw:
                address = location.raw['address']
                city = address.get('city') or address.get('town') or address.get('village') or "Bilinmiyor"
            else:
                city = "Bilinmiyor"

            if request.user.is_authenticated:
                profile, _ = Profile.objects.get_or_create(user=request.user)
                profile.city = city
                profile.latitude = lat
                profile.longitude = lng
                profile.save()

            return JsonResponse({
                "success": True,
                "city": city
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST yöntemi gerekli."}, status=405)
from .utils import tahmini_saat_ozeti, haftalik_grafik_verisi, uygun_saat_onerisi



from django.shortcuts import render
from .models import Appointment
from accounts.models import Profile  # Profile modeli burada yer alıyorsa
from .utils import tahmini_saat_ozeti  # AI öneri fonksiyonun buysa

@login_required
def panel_view(request):
    profile = Profile.objects.get(user=request.user)
    city = profile.city if profile.city else None

    if city:
        randevular = Appointment.objects.filter(salon__city=city, user=request.user)
    else:
        randevular = Appointment.objects.filter(user=request.user)

    tahmin = tahmini_saat_ozeti(request.user)
    haftalik = haftalik_grafik_verisi(request.user)
    uygun_saatler = uygun_saat_onerisi(request.user)

    return render(request, 'appointments/kullanici_paneli.html', {
        'randevular': randevular,
        'tahmin': tahmin,
        'haftalik': haftalik,
        'uygun_saatler': uygun_saatler,
    })

from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from .utils import haftalik_grafik_verisi

@login_required
def grafik_pdf_view(request):
    data = haftalik_grafik_verisi(request.user)
    html_string = render_to_string('appointments/grafik_pdf.html', {
        'haftalik': data,
        'user': request.user
    })
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="haftalik-grafik.pdf"'
    return response

from collections import defaultdict
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.timezone import localdate
from datetime import timedelta

from .models import Salon, Appointment


@login_required
def aylik_rapor_pdf(request, salon_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    
    salon = Salon.objects.get(id=salon_id)
    today = localdate()
    start = today.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Günlük randevu sayısı
    veriler = []
    for i in range(1, end.day + 1):
        tarih = start.replace(day=i)
        sayi = Appointment.objects.filter(
            salon=salon,
            appointment_date__date=tarih
        ).count()
        veriler.append((tarih.strftime('%d %B'), sayi))

    html = render_to_string("appointments/rapor_pdf.html", {
        'salon': salon,
        'today': today,
        'veriler': veriler,
    })

    pdf_file = HTML(string=html).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{salon.name}-rapor.pdf"'
    return response

from collections import defaultdict
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse

@login_required
def kategori_rapor_pdf(request, salon_id):
    salon = Salon.objects.get(id=salon_id)

    # 🔒 Kullanıcı kontrolü:
    if salon.user != request.user:
        return HttpResponseForbidden("❌ Bu rapora erişim yetkiniz yok.")

    randevular = Appointment.objects.filter(salon=salon).order_by('category', 'appointment_date')
    gruplu = defaultdict(list)
    for r in randevular:
        gruplu[r.category].append(r)

    html = render_to_string("appointments/kategori_raporu.html", {
        'salon': salon,
        'gruplu': dict(gruplu),
    })
    pdf = HTML(string=html).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{salon.name}-kategori-raporu.pdf"'
    return response

import tempfile
import zipfile
from django.http import FileResponse

@login_required
def zip_pdf_raporlar(request, salon_id):
    if salon.user != request.user:
        return HttpResponseForbidden()
    salon = Salon.objects.get(id=salon_id)
    haftalik_html = render_to_string("appointments/grafik_pdf.html", {
        'salon': salon,
        'haftalik': haftalik_grafik_verisi(request.user),
        'user': request.user,
    })

    aylik_html = render_to_string("appointments/rapor_pdf.html", {
        'salon': salon,
        'today': localdate(),
        'veriler': [(f"Gün {i}", i) for i in range(1, 8)],  # Örnek veri
        'request': request
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        haftalik_path = f"{tmpdir}/haftalik.pdf"
        aylik_path = f"{tmpdir}/aylik.pdf"
        zip_path = f"{tmpdir}/raporlar.zip"

        HTML(string=haftalik_html).write_pdf(haftalik_path)
        HTML(string=aylik_html).write_pdf(aylik_path)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(haftalik_path, "haftalik.pdf")
            zipf.write(aylik_path, "aylik.pdf")

        return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename="raporlar.zip")

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

@login_required
def pdf_mail_gonder(request, salon_id):
    if salon.user != request.user:
     return HttpResponseForbidden()
    salon = Salon.objects.get(id=salon_id)
    user = request.user
    today = localdate()

    html = render_to_string("appointments/rapor_pdf.html", {
        'salon': salon,
        'today': today,
        'veriler': [(f"Gün {i}", i) for i in range(1, 8)],
        'request': request
    })

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        HTML(string=html).write_pdf(target=output.name)

        mail = EmailMessage(
            subject=f"{salon.name} - Aylık Rapor",
            body="Randevu raporunuz ekte PDF olarak gönderilmiştir.",
            from_email="noreply@khsapp.com",
            to=[user.email]
        )
        mail.attach("aylik_rapor.pdf", output.read(), "application/pdf")
        mail.send()

    return HttpResponse("📩 PDF mail ile gönderildi.")

@login_required
def reel_detail(request, id):
    reel = get_object_or_404(ReelPost, id=id)
    comments = reel.comments.all().order_by('-created_at')
    form = ReelCommentForm()

    if request.method == 'POST':
        form = ReelCommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.reel = reel
            new_comment.user = request.user
            new_comment.save()
            return redirect('appointments:reel_detail', id=reel.id)

    return render(request, 'salon/reel_detail.html', {
        'reel': reel,
        'comments': comments,
        'form': form
    })
# views.py dosyası
from django.shortcuts import render
from .models import SalonComment

def salon_comments(request):
    # Salon yorumlarını veritabanından alıyoruz
    comments = SalonComment.objects.all()
    # Yorumları template'e gönderiyoruz
    return render(request, 'salon_comments.html', {'comments': comments})


from django.http import JsonResponse
from .models import ReelLike

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(ReelPost, id=post_id)
    liked, created = ReelLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        liked.delete()
        return JsonResponse({'liked': False, 'count': post.likes.count()})
    return JsonResponse({'liked': True, 'count': post.likes.count()})

# views.py (düzenlenmiş)
from django.shortcuts import render, redirect

from django.contrib import messages
from .models import Salon, SalonPost, SalonMedia

@login_required
def upload_anlik(request):
    if request.method == "POST":
        caption = request.POST.get('caption', '')
        files = request.FILES.getlist('media_files')

        salon = Salon.objects.filter(user=request.user).first()
        if not salon:
            messages.error(request, "Salon profili bulunamadı. Lütfen önce salon bilgilerinizi girin.")
            return redirect('appointments:profile')  # Veya uygun bir sayfa

        post = SalonPost.objects.create(salon=salon, description=caption)

        for file in files:
            ext = file.name.split('.')[-1].lower()
            media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
            SalonMedia.objects.create(post=post, media_file=file, type=media_type)

        messages.success(request, "Paylaşım başarıyla yüklendi.")
        return redirect('appointments:reels_list')

    return render(request, 'salon/upload_post.html')


from django.shortcuts import render
from .models import AnlikPaylasim

@login_required
def post_list(request):
    user = request.user
    posts = AnlikPaylasim.objects.filter(salon__user=user).order_by('-created_at')
    return render(request, 'appointments/post_list.html', {'posts': posts})

from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.models import Profile
from accounts.forms import ProfileUpdateForm  # ✅ Doğru


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'form': form})

# appointments/views.py
from django.shortcuts import render, redirect
from .forms import SalonMediaForm
from .models import SalonMedia, SalonPost
from django.contrib.auth.decorators import login_required

@login_required
def upload_post(request):
    if request.method == 'POST':
        form = SalonMediaForm(request.POST, request.FILES)
        files = request.FILES.getlist('media_files')

        if form.is_valid() and files:
            salon_post = SalonPost.objects.filter(user=request.user).first()
            for media_file in files:
                ext = media_file.name.split('.')[-1].lower()
                media_type = 'video' if ext in ['mp4', 'mov', 'avi'] else 'image'
                SalonMedia.objects.create(
                    post=salon_post,
                    media_file=media_file,
                    type=media_type
                )
            return redirect('appointments:reels_list')
    else:
        form = SalonMediaForm()

    return render(request, 'appointments/upload_post.html', {'form': form})

# appointments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Appointment
from .forms import AppointmentForm

def update_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('appointments:appointment_detail', id=appointment.id)
    else:
        form = AppointmentForm(instance=appointment, user=request.user)
    return render(request, 'appointments/update_appointment.html', {'form': form, 'appointment': appointment})
