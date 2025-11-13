from rest_framework import serializers
from .models import Announcement, UserAnnouncement


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["id", "title", "description", "created_at"]


class UserAnnouncementSerializer(serializers.ModelSerializer):
    announcement = AnnouncementSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserAnnouncement
        fields = [
            "id",
            "announcement",
            "created_at",
            "email_sent_at",
            "email_delivered_at",
            "status",
        ]

    def get_status(self, obj):
        if obj.email_sent_at:
            return "sent"
        if obj.email_last_error:
            return "failed"
        return "pending"
