from datetime import datetime as dt, timedelta
from django.db.models import Count
from django.db.models.functions import ExtractHour, TruncDate
from django.utils.timezone import now, make_aware, localdate, localtime
from .models import Appointment, Salon
import pandas as pd
from django.contrib.auth.models import User
from appointments.models import Salon
from django.contrib.auth import get_user_model
CustomUser = get_user_model()

def tahmini_saat_ozeti(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return None  # Eğer salon yoksa hata çıkmasın

    qs = Appointment.objects.filter(salon=salon)

    saatler = (
        qs.annotate(saat=ExtractHour('appointment_date'))
          .values('saat')
          .annotate(toplam=Count('id'))
          .order_by('-toplam')
    )
    if saatler:
        return f"{saatler[0]['saat']:02d}:00"
    return None

from datetime import datetime as dt, timedelta
from django.utils.timezone import make_aware, now
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractHour
from .models import Appointment, Salon

# ✅ En uygun boş saatler
def en_uygun_saatler(tarih, user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return []

    saat_listesi = [f"{s:02d}:00" for s in range(9, 20)]
    uygunlar = []

    for saat_str in saat_listesi:
        saat_obj = dt.combine(tarih, dt.strptime(saat_str, "%H:%M").time())
        saat_obj = make_aware(saat_obj)
        if not Appointment.objects.filter(appointment_date=saat_obj, salon=salon).exists():
            uygunlar.append(saat_str)

    return uygunlar[:3]

# ✅ Haftalık çubuk grafik verisi
def haftalik_gunluk_randevu_sayisi(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return []

    bugun = now().date()
    yedi_gun_once = bugun - timedelta(days=6)

    qs = Appointment.objects.filter(
        salon=salon,
        appointment_date__date__range=(yedi_gun_once, bugun)
    )

    qs = (
        qs.annotate(gun=TruncDate('appointment_date'))
          .values('gun')
          .annotate(adet=Count('id'))
          .order_by('gun')
    )

    gun_isimleri = {0: 'Pzt', 1: 'Salı', 2: 'Çrş', 3: 'Perş', 4: 'Cuma', 5: 'Cmt', 6: 'Paz'}
    veri = []
    for i in range(7):
        tarih = yedi_gun_once + timedelta(days=i)
        gun = tarih.weekday()
        adet = next((item['adet'] for item in qs if item['gun'] == tarih), 0)
        veri.append({'gun': gun_isimleri[gun], 'adet': adet})
    
    return veri

# ✅ Bugünkü saat yoğunluğu
def gunluk_saat_istatistigi(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return []

    bugun = now().date()
    qs = Appointment.objects.filter(salon=salon, appointment_date__date=bugun)

    saatler = (
        qs.annotate(saat=ExtractHour('appointment_date'))
        .values('saat')
        .annotate(sayi=Count('id'))
        .order_by('saat')
    )

    return [{'saat': f"{s['saat']:02d}:00", 'adet': s['sayi']} for s in saatler]

def en_yogun_saat_araligi(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return None

    qs = Appointment.objects.filter(salon=salon)
    qs = (
        qs.annotate(hour=ExtractHour('appointment_date'))
           .values('hour')
           .annotate(count=Count('id'))
           .order_by('-count')
    )
    if qs:
        saat = qs[0]['hour']
        return f"{saat:02d}:00 - {saat+1:02d}:00"
    return None

import pandas as pd
from django.utils.timezone import localtime
from .models import Appointment, Salon

def tahmin_motoru(user):
    # Kullanıcıya ait salonu al
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return None  # Kullanıcının salonu yoksa

    # Randevuları getir
    randevular = Appointment.objects.filter(salon=salon)
    if not randevular.exists():
        return None  # Randevu yoksa

    # Randevuları gün ve saat bazında listele
    data = []
    for r in randevular:
        local_dt = localtime(r.appointment_date)
        data.append({
            'day': local_dt.strftime('%A'),
            'hour': local_dt.hour
        })

    # Pandas ile analiz
    df = pd.DataFrame(data)
    if df.empty:
        return None

    # Gün ve saat kombinasyonlarını grupla, en sık olanı seç
    day_hour_stats = (
        df.groupby(['day', 'hour'])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # En yoğun gün ve saat
    best_day = day_hour_stats.iloc[0]['day']
    best_hour = int(day_hour_stats.iloc[0]['hour'])

    return {
        "gun": best_day,
        "saat": f"{best_hour:02d}:00"
    }

import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.utils.timezone import localdate
from datetime import timedelta
from collections import Counter
from .models import Appointment

import matplotlib.pyplot as plt
from collections import Counter
from io import BytesIO
import base64
from django.utils.timezone import localdate
from .models import Appointment  # Eğer aynı dosyadaysa

def randevu_aylik_grafik_base64(user):
    today = localdate()
    start_date = today.replace(day=1)
    end_date = today

    # Bu ayki randevular
    appointments = Appointment.objects.filter(
        user=user,
        appointment_date__date__range=(start_date, end_date)
    )

    # Gün bazlı sayım
    gun_sayilari = Counter([a.appointment_date.day for a in appointments])
    gunler = sorted(gun_sayilari.keys())
    sayilar = [gun_sayilari[gun] for gun in gunler]

    # Grafik oluştur
    plt.figure(figsize=(7, 3))
    plt.bar(gunler, sayilar, color='skyblue')
    plt.title("📅 Aylık Randevu Dağılımı")
    plt.xlabel("Gün")
    plt.ylabel("Randevu Sayısı")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    # Base64'e çevir
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return image_base64

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from django.utils.timezone import localdate

def send_ai_summary_email(user):
    tahmin = tahmini_saat_ozeti(user)
    en_yogun = en_yogun_saat_araligi(user)
    bu_ay = bu_ay_en_sik_saat(user)
    grafik = randevu_aylik_grafik_base64(user)

    context = {
        'user': user,
        'tahmin': tahmin,
        'en_yogun': en_yogun,
        'bu_ay': bu_ay,
        'grafik': grafik,
        'tarih': localdate()
    }

    html_message = render_to_string('emails/ai_summary.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='🧠 Yapay Zekâ Haftalık Analiz Özeti',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )

# utils.py
from io import BytesIO
import zipfile
from io import BytesIO
from django.http import HttpResponse
from weasyprint import HTML
from django.template.loader import render_to_string

def generate_pdf_from_appointment(randevu):
    html_string = render_to_string("appointments/randevu_pdf.html", {"randevu": randevu})
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_file)
    pdf_file.seek(0)
    return pdf_file

def zip_randevular_pdf(queryset):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for r in queryset:
            pdf_bytes = generate_pdf_from_appointment(r)
            zip_file.writestr(f"randevu_{r.id}.pdf", pdf_bytes.getvalue())
    buffer.seek(0)
    return buffer.getvalue()

# utils.py (devam)
import matplotlib.pyplot as plt
import base64

def gunluk_grafik_png(queryset):
    saatler = [r.appointment_date.hour for r in queryset]
    plt.figure(figsize=(6, 3))
    plt.hist(saatler, bins=range(8, 21), color='skyblue', edgecolor='black')
    plt.title("Günlük Randevu Dağılımı")
    plt.xlabel("Saat")
    plt.ylabel("Randevu Sayısı")

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf.getvalue()

from io import BytesIO
import zipfile
from weasyprint import HTML
from django.template.loader import render_to_string

def toplu_pdf_olustur(randevu_queryset):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for randevu in randevu_queryset:
            html = render_to_string("appointments/randevu_pdf.html", {"randevu": randevu})
            pdf_io = BytesIO()
            HTML(string=html).write_pdf(target=pdf_io)
            pdf_io.seek(0)
            zip_file.writestr(f"randevu_{randevu.id}.pdf", pdf_io.read())
    buffer.seek(0)
    return buffer

import base64
import matplotlib.pyplot as plt

def gunluk_grafik_base64(queryset):
    from io import BytesIO

    saatler = [r.appointment_date.hour for r in queryset]
    plt.figure(figsize=(6, 3))
    plt.hist(saatler, bins=range(8, 21), color='skyblue', edgecolor='black')
    plt.title("Günlük Randevu Dağılımı")
    plt.xlabel("Saat")
    plt.ylabel("Randevu Sayısı")

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_base64

from datetime import datetime, time, timedelta
from django.utils.timezone import make_aware
from .models import Appointment

def en_bos_saat(tarih, user=None):
    saatler = [time(h, 0) for h in range(9, 20)]
    en_bos = None
    min_adet = None

    for saat in saatler:
        dt = make_aware(datetime.combine(tarih, saat))
        adet = Appointment.objects.filter(appointment_date=dt).count()

        if min_adet is None or adet < min_adet:
            min_adet = adet
            en_bos = saat

    return en_bos.strftime("%H:%M") if en_bos else "Yok"

from django.utils.timezone import localdate
from django.db.models.functions import ExtractHour
from django.db.models import Count

def bu_ay_en_sik_saat(user):
    salon = Salon.objects.filter(user=user).first()
    if not salon:
        return None

    today = localdate()
    ay_baslangic = today.replace(day=1)

    qs = Appointment.objects.filter(
        salon=salon,
        appointment_date__date__gte=ay_baslangic
    )

    saatler = (
        qs.annotate(saat=ExtractHour('appointment_date'))
        .values('saat')
        .annotate(toplam=Count('id'))
        .order_by('-toplam')
    )

    if saatler:
        return f"{saatler[0]['saat']:02d}:00"
    return None

from django.utils.timezone import localdate
from datetime import timedelta
from .models import Appointment
from collections import Counter

# 📈 Haftalık yoğunluk verisi
def haftalik_grafik_verisi(user):
    today = localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    counts = []

    for day in days:
        count = Appointment.objects.filter(
            user=user,
            appointment_date__date=day
        ).count()
        counts.append((day.strftime('%a'), count))

    return counts

# 🤖 En uygun 3 saat
def uygun_saat_onerisi(user):
    today = localdate()
    saatler = [f"{h:02d}:00" for h in range(9, 21)]
    dolu_saatler = Appointment.objects.filter(
        user=user,
        appointment_date__date=today
    ).values_list('appointment_date__hour', flat=True)

    sayac = Counter(dolu_saatler)
    bos_saatler = [s for s in saatler if int(s.split(':')[0]) not in sayac]
    return bos_saatler[:3]  # ilk 3 uygun saat
# appointments/utils.py

import json
import random
from datetime import datetime
import os
from django.conf import settings

def yapay_zeka_muzik_sec(kategori=None, ruh_hali=None):
    saat = datetime.now().hour
    json_path = os.path.join(settings.BASE_DIR, 'music_library.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        muzikler = json.load(f)

    filtreli = []

    for muzik in muzikler:
        if kategori and kategori in muzik['genre']:
            filtreli.append(muzik)
        elif ruh_hali and ruh_hali in muzik['mood']:
            filtreli.append(muzik)
        elif saat >= 20 and "gece" in muzik['mood']:
            filtreli.append(muzik)
        elif saat < 12 and "sakin" in muzik['mood']:
            filtreli.append(muzik)

    if not filtreli:
        filtreli = muzikler

    secilen = random.choice(filtreli)
    return secilen['file']







