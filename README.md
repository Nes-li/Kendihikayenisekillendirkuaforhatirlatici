# Kuaför Hatırlatıcı 💇‍♀️📅

Bu proje, kuaförler için yapay zekâ destekli bir **randevu, medya ve müşteri yönetim sistemi** sunar. Django tabanlıdır, mobil uyumludur ve Google Play'e entegre edilecek şekilde tasarlanmıştır.

## 🔥 Temel Özellikler

 1. 🧱 Temel Yapı
- Django kurulumu, `appointments` ve `accounts` app'leri
- Admin panel özelleştirmesi

 2. 📅 Randevu Sistemi
- CRUD: ekle, listele, düzenle, sil
- Aynı saate randevu çakışma kontrolü
- Kategorili randevular (Kesim, Boya, Fön)

 3. 👤 Kullanıcı Yönetimi
- Kayıt olma, giriş, çıkış, şifre değiştirme
- Profil düzenleme ve avatar yükleme
- Google ile giriş
- Kullanıcı şehir kaydı (konum bazlı)

 4. 🎨 Tasarım & Tema
- Bootstrap tabanlı responsive tasarım
- Karanlık/Açık tema (dark mode)
- Mobil menü (hamburger)
- Altın başlıklı ana sayfa tasarımı
- “+ Randevu Ekle” sabit mobil buton

 5. 🧾 PDF & ZIP İşlemleri
- WeasyPrint & xhtml2pdf destekli çıktılar
- Haftalık/aylık grafik + tablo PDF’leri
- PDF’lerin ZIP arşivine dönüşmesi
- Admin panelden toplu PDF indir
- E-posta ile otomatik PDF gönderme
- Tarih ve şehir bazlı PDF filtreleme

 6. 📊 Takvim ve Grafikler
- FullCalendar.js ile takvim görünümü
- Renkli randevu etiketleri
- Günlük, haftalık, aylık istatistik grafikleri
- Takvime tıklanabilir modal detay
- Grafiklerin PDF çıktısı

 7. 🤖 Yapay Zeka Özellikleri
- Günlük en uygun 3 saat önerisi
- Haftalık yoğunluk analizi
- AI sohbet tarzı öneriler
- Yapay zekâ sesli okuma desteği

 8. 🎥 Reels (Tanıtım Medyası)
- Çoklu video/resim yükleme
- Reels listesi ve galeri görünümü
- ❤ Beğeni, 💬 Yorum, ⭐ Favori sistemi
- 🎯 Etiket filtreleme
- Öne çıkan altın çerçeveli reels tasarımı
- AI ile otomatik müzik seçimi

 9. 📍 Konum & Filtreleme
- Şehir bilgisi alma (JavaScript + Django)
- Kullanıcı profiline şehir kaydetme
- Şehir bazlı salon filtreleme
- Google Maps iframe ile harita gösterimi

 10. ⚙️ Admin Panel
- admin-interface özelleştirmesi
- Salon bazlı yönetim ve öne çıkan içerikler
- PDF/ZIP erişimi ve istatistikler

 11. ☁️ Yayınlama & Mobil
- PythonAnywhere canlı sunucu
- WebView tabanlı Android uygulama
- Google Play için APK hazırlığı (Splash, SEO, vs.)

---

 🚀 Kurulum

```bash
git clone https://github.com/KULLANICIADIN/kuaforhatirlatici.git
cd kuaforhatirlatici
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
