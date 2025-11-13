from django.db import models
from django.contrib.auth import get_user_model

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
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_delivered_at = models.DateTimeField(null=True, blank=True)
    email_send_attempts = models.PositiveIntegerField(default=0)
    email_last_error = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.announcement.title}"

    class Meta:
        unique_together = ("announcement", "user")
        ordering = ("-created_at",)

    @property
    def has_sent_email(self) -> bool:
        return self.email_sent_at is not None

    def send_email(self, *, force: bool = False) -> bool:
        from .emails import send_user_announcement_email

        return send_user_announcement_email(self, force=force)
