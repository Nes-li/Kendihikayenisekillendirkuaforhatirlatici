from django.db import models
from django.contrib.auth import get_user_model
from appointments.reel_post import ReelPost


User = get_user_model()

class ReelComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(ReelPost, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
