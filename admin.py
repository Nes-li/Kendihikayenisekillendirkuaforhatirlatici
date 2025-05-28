from django.contrib import admin
from .models import (
    Appointment, Salon, SalonMedia, BackgroundMusic,
    SalonComment, ReelPost, ReelComment, ReelsMedia
)
from django.utils.html import format_html

# ---- Appointment ----
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'phone_number', 'appointment_date', 'get_salon_name', 'category', 'user')
    search_fields = ('customer_name', 'salon__name', 'phone_number')
    list_filter = ('category', 'appointment_date', 'salon__name')

    def get_salon_name(self, obj):
        return obj.salon.name if obj.salon else "No Salon"
    get_salon_name.short_description = 'Salon Adı'

# ---- SalonMedia ----
@admin.register(SalonMedia)
class SalonMediaAdmin(admin.ModelAdmin):
    list_display = ('get_post_info', 'media_preview', 'type', 'get_caption', 'created_at')
    readonly_fields = ('media_preview',)

    def get_post_info(self, obj):
        return str(obj.post)
    get_post_info.short_description = "Post"

    def get_caption(self, obj):
        return obj.post.description
    get_caption.short_description = "Açıklama"

    def media_preview(self, obj):
        if obj.media_file:
            if obj.type == 'image':
                return format_html('<img src="{}" style="height:100px;" />', obj.media_file.url)
            elif obj.type == 'video':
                return format_html('<video src="{}" style="height:100px;" controls />', obj.media_file.url)
        return "Önizleme yok"
    media_preview.short_description = 'Önizleme'

# ---- ReelPost ----
@admin.register(ReelPost)
class ReelPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'salon', 'created_at', 'like_sayisi', 'yorum_sayisi')
    search_fields = ('title', 'salon__name')
    list_filter = ('created_at',)

    def like_sayisi(self, obj):
        return obj.reellike_set.count()
    like_sayisi.short_description = "Beğeni"

    def yorum_sayisi(self, obj):
        return obj.reelcomment_set.count()
    yorum_sayisi.short_description = "Yorum"

# ---- SalonComment ----
@admin.register(SalonComment)
class SalonCommentAdmin(admin.ModelAdmin):
    list_display = ('salon', 'user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('salon__name', 'user__username', 'comment')

# ---- ReelsMedia ----
@admin.register(ReelsMedia)
class ReelsMediaAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_file', 'type', 'created_at', 'media_preview')
    search_fields = ('post__title',)

    def media_preview(self, obj):
        if obj.type == 'image' and obj.media_file:
            return format_html('<img src="{}" style="height:100px;" />', obj.media_file.url)
        elif obj.type == 'video' and obj.media_file:
            return format_html('<video src="{}" style="height:100px;" controls />', obj.media_file.url)
        return "No Preview"
    media_preview.short_description = 'Preview'

# ---- Admin panel başlığı ----
admin.site.site_title = "Kuaför Yönetimi"
admin.site.site_header = "Kendi Hikâyeni Şekillendir"
admin.site.index_title = "Randevu Kontrol Paneli"
