import pytest
from django.utils import timezone

from accounts.models import User
from announcement.models import Announcement, UserAnnouncement
from announcement.serializers import UserAnnouncementSerializer


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="serializer@example.com",
        password="pass1234",
        national_code="2234567890",
        phone_number="09122222222",
        gender="F",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(title="Schedule", description="New schedule")


@pytest.mark.django_db
def test_user_announcement_serializer_status_variants(user, announcement):
    sent = UserAnnouncement.objects.create(
        user=user,
        announcement=announcement,
        email_sent_at=timezone.now(),
    )
    announcement_failed = Announcement.objects.create(title="Issue", description="")
    failed = UserAnnouncement.objects.create(
        user=user,
        announcement=announcement_failed,
        email_last_error="SMTP down",
    )
    announcement_pending = Announcement.objects.create(title="Later", description="")
    pending = UserAnnouncement.objects.create(user=user, announcement=announcement_pending)

    serializer = UserAnnouncementSerializer([sent, failed, pending], many=True)

    statuses = [item["status"] for item in serializer.data]
    assert statuses == ["sent", "failed", "pending"]
    assert serializer.data[0]["announcement"]["title"] == "Schedule"
