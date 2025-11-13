import pytest
from django.db import transaction

from accounts.models import User
from announcement.models import Announcement, UserAnnouncement


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="signal@example.com",
        password="pass1234",
        national_code="4434567890",
        phone_number="09144444444",
        gender="M",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(title="Signal", description="Triggered")


@pytest.mark.django_db(transaction=True)
def test_signal_sends_email_on_commit(monkeypatch, user, announcement):
    calls = []

    def fake_send(instance, *, force=False):
        calls.append((instance.pk, force))
        return True

    monkeypatch.setattr("announcement.signals.send_user_announcement_email", fake_send)

    with transaction.atomic():
        ua = UserAnnouncement.objects.create(user=user, announcement=announcement)
        assert calls == []

    assert calls == [(ua.pk, False)]


@pytest.mark.django_db(transaction=True)
def test_signal_ignores_updates(monkeypatch, user, announcement):
    calls = []

    def fake_send(instance, *, force=False):
        calls.append((instance.pk, force))
        return True

    monkeypatch.setattr("announcement.signals.send_user_announcement_email", fake_send)

    ua = UserAnnouncement.objects.create(user=user, announcement=announcement)
    assert calls == [(ua.pk, False)]
    calls.clear()

    with transaction.atomic():
        ua.email_last_error = "err"
        ua.save(update_fields=["email_last_error"])

    assert calls == []
