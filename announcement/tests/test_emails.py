from datetime import timedelta

import pytest
from django.core import mail
from django.db.models.signals import post_save
from django.utils import timezone

from accounts.models import User
from announcement.emails import (
    build_email_subject,
    render_announcement_html,
    send_user_announcement_email,
)
from announcement.models import Announcement, UserAnnouncement
from announcement.signals import send_user_announcement_when_created


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="emailtest@example.com",
        password="pass1234",
        national_code="1234567899",
        phone_number="09111111111",
        gender="M",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(
        title="Markdown intro",
        description="**Bold** _Italic_",
    )


@pytest.fixture(autouse=True)
def disable_auto_email_signal():
    post_save.disconnect(send_user_announcement_when_created, sender=UserAnnouncement)
    yield
    post_save.connect(send_user_announcement_when_created, sender=UserAnnouncement)


@pytest.fixture
def user_announcement(user, announcement):
    return UserAnnouncement.objects.create(user=user, announcement=announcement)


def test_render_announcement_html_converts_markdown(announcement):
    html = render_announcement_html(announcement)
    assert "<strong>Bold</strong>" in html
    assert "<em>Italic</em>" in html


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Important Update", "اطلاعیه: Important Update"),
        ("", "اطلاعیه جدید"),
        (None, "اطلاعیه جدید"),
    ],
)
def test_build_email_subject_handles_missing_titles(title, expected):
    announcement = Announcement(title=title)
    assert build_email_subject(announcement) == expected


@pytest.mark.django_db(transaction=True)
def test_send_user_announcement_email_skips_when_user_email_missing(user_announcement):
    user_announcement.user.email = None
    result = send_user_announcement_email(user_announcement)

    assert result is False
    user_announcement.refresh_from_db()
    assert user_announcement.email_send_attempts == 0
    assert user_announcement.email_sent_at is None


@pytest.mark.django_db(transaction=True)
def test_send_user_announcement_email_records_failure(monkeypatch, user_announcement):
    def failing_send(self):
        raise RuntimeError("SMTP failure")

    monkeypatch.setattr("announcement.emails.EmailMultiAlternatives.send", failing_send)

    with pytest.raises(RuntimeError):
        send_user_announcement_email(user_announcement, force=True)

    user_announcement.refresh_from_db()
    assert user_announcement.email_send_attempts == 1
    assert user_announcement.email_last_error == "SMTP failure"
    assert user_announcement.email_sent_at is None
    assert user_announcement.email_delivered_at is None


@pytest.mark.django_db(transaction=True)
def test_send_user_announcement_email_updates_timestamps(settings, user_announcement):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    send_user_announcement_email(user_announcement, force=True)

    user_announcement.refresh_from_db()
    assert user_announcement.email_sent_at is not None
    assert user_announcement.email_delivered_at is not None
    assert user_announcement.email_last_error == ""
    assert user_announcement.email_send_attempts == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
def test_send_user_announcement_email_force_resends(settings, user_announcement):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    send_user_announcement_email(user_announcement)
    first_sent = user_announcement.email_sent_at

    # pretend the send happened two minutes ago to assert timestamp updates
    UserAnnouncement.objects.filter(pk=user_announcement.pk).update(
        email_sent_at=timezone.now() - timedelta(minutes=2)
    )
    user_announcement.refresh_from_db()

    send_user_announcement_email(user_announcement, force=True)

    user_announcement.refresh_from_db()
    assert user_announcement.email_sent_at >= first_sent
    assert len(mail.outbox) == 2
