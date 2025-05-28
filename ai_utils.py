import pandas as pd
from django.utils.timezone import localtime
from appointments.models import Salon
from appointments.models import Appointment, Salon

def tahmin_motoru(user):
    salon = Salon.objects.filter(user=user).first()  # 💡 sadece ilkini al
    if not salon:
        return "Veri yok"
    
    # ... diğer analiz kodların devam eder


    # Bu salonun tüm randevularını al
    randevular = Appointment.objects.filter(salon=salon)
    if not randevular.exists():
        return None  # Hiç randevu yoksa analiz yapılamaz

    # Her randevuyu gün ve saat olarak listele
    data = []
    for r in randevular:
        local_dt = localtime(r.appointment_date)  # Zamanı yerel saate çevir
        data.append({
            'day': local_dt.strftime('%A'),  # Örn: Monday
            'hour': local_dt.hour            # Örn: 14
        })

    # DataFrame'e dönüştür
    df = pd.DataFrame(data)
    if df.empty:
        return None  # Güvenlik için tekrar kontrol

    # Gün + Saat'e göre grup oluştur, en çok tekrar eden saati bul
    day_hour_stats = (
        df.groupby(['day', 'hour'])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # En yoğun günü ve saati al
    best_day = day_hour_stats.iloc[0]['day']
    best_hour = int(day_hour_stats.iloc[0]['hour'])

    # Sonuç: {"gun": "Tuesday", "saat": "14:00"}
    return {
        "gun": best_day,
        "saat": f"{best_hour:02d}:00"
    }