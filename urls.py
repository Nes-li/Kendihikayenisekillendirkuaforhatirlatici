"""
URL configuration for kuaforhatirlatici project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# kuaforhatirlatici/urls.py

# kuaforhatirlatici/urls.py

from django.contrib import admin
from django.urls import path, include
from appointments.views import home_view, haftalik_grafik_view
from django.conf import settings
from django.conf.urls.static import static
from appointments.views import toggle_theme

urlpatterns = [
    # Admin paneli
    path('admin/', admin.site.urls),
    
    # Kendi accounts app'inin URL'leri (BUNU EKLEDİK)
    path('accounts/', include('accounts.urls')),# Bunu ekle!

    # Hesap işlemleri (Login, Register vb.)
    path('accounts/social/', include('allauth.urls')),# Allauth URL'lerini ekliyoruz

    # Randevular
    path('appointments/', include('appointments.urls', namespace='appointments')),
    
   # path('axes/', include('axes.urls')),
    # urls.py
    path('gizliadmin/', admin.site.urls),

    # Grafik sayfası
    path('grafik/', haftalik_grafik_view, name='haftalik_grafik'),

    # Temayı değiştirme (örneğin, dark mode vs.)
    path('toggle-theme/', toggle_theme, name='toggle_theme'),

    # Çok dilli destek (i18n)
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Anasayfa
    path('', home_view, name='home'),
]

# Medya dosyalarını geliştirme sırasında sunmak için
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
