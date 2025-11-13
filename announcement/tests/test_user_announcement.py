import pytest
from django.core import mail

from accounts.models import User
from announcement.emails import send_user_announcement_email
from announcement.models import Announcement, UserAnnouncement


@pytest.fixture
def user(db):
    return User.objects.create_user(email="member@example.com", password="pass1234")


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(
        title="خبر فوری",
        description="**سلام!** این یک اطلاعیه *جدید* است.",
    )


@pytest.mark.django_db(transaction=True)
def test_email_is_sent_on_user_announcement_creation(settings, user, announcement):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    user_announcement = UserAnnouncement.objects.create(user=user, announcement=announcement)
    user_announcement.refresh_from_db()

    assert user_announcement.email_sent_at is not None
    assert user_announcement.email_send_attempts == 1
    assert len(mail.outbox) == 1
    html_body = mail.outbox[0].alternatives[0][0]
    assert "<strong>سلام!</strong>" in html_body
    assert "<em>جدید</em>" in html_body


@pytest.mark.django_db(transaction=True)
def test_force_resend_sends_again(settings, user, announcement):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    user_announcement = UserAnnouncement.objects.create(user=user, announcement=announcement)
    user_announcement.refresh_from_db()

    # sending without force should skip once already sent
    mail.outbox = []
    assert send_user_announcement_email(user_announcement) is False
    assert len(mail.outbox) == 0

    # forcing should send again and update timestamps
    previous_sent_at = user_announcement.email_sent_at
    assert send_user_announcement_email(user_announcement, force=True) is True
    user_announcement.refresh_from_db()

    assert len(mail.outbox) == 1
    assert user_announcement.email_sent_at >= previous_sent_at
    assert user_announcement.email_send_attempts >= 2
    assert user_announcement.email_last_error == ""
