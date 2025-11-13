import pytest
from django.utils import timezone

from accounts.models import User
from announcement.models import Announcement, UserAnnouncement


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="model@example.com",
        password="pass1234",
        national_code="1234567890",
        phone_number="09100000000",
        gender="M",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(title="Site Update", description="**Hi** there!")


@pytest.mark.django_db
def test_user_announcement_str(user, announcement):
    user_announcement = UserAnnouncement.objects.create(user=user, announcement=announcement)
    assert str(user_announcement) == "model@example.com - Site Update"


@pytest.mark.django_db
def test_user_announcement_has_sent_email(user, announcement):
    user_announcement = UserAnnouncement.objects.create(user=user, announcement=announcement)
    assert user_announcement.has_sent_email is False

    user_announcement.email_sent_at = timezone.now()
    assert user_announcement.has_sent_email is True


@pytest.mark.django_db
def test_user_announcement_send_email_delegates(monkeypatch, user, announcement):
    user_announcement = UserAnnouncement.objects.create(user=user, announcement=announcement)

    captured = {}

    def fake_send(instance, *, force=False):
        captured["called_with"] = (instance, force)
        return "ok"

    monkeypatch.setattr("announcement.emails.send_user_announcement_email", fake_send)

    result = user_announcement.send_email(force=True)

    assert result == "ok"
    assert captured["called_with"] == (user_announcement, True)
