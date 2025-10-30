from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from django.db.models import QuerySet

User = get_user_model()


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserAnnouncement(models.Model):
    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE, related_name="user_announcements"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.announcement.title}"
