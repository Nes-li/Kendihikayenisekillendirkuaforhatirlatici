from django.db import models

class BackgroundMusic(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='music/')
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return self.title
