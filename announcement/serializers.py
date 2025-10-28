from rest_framework import serializers
from .models import Announcement, UserAnnouncement


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["id", "title", "description", "created_at"]


class UserAnnouncementSerializer(serializers.ModelSerializer):
    announcement = AnnouncementSerializer(read_only=True)

    class Meta:
        model = UserAnnouncement
        fields = ["id", "announcement", "created_at"]
