import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from accounts.models import User
from announcement.admin import AnnouncementAdmin, UserAnnouncementAdmin
from announcement.models import Announcement, UserAnnouncement


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def staff_user(db):
    return User.objects.create_superuser(
        email="staff@example.com",
        password="pass1234",
        national_code="5554567890",
        phone_number="09155555555",
        gender="M",
    )


@pytest.fixture
def announcement(db):
    return Announcement.objects.create(title="Promo", description="Sale")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="target@example.com",
        password="pass1234",
        national_code="6664567890",
        phone_number="09166666666",
        gender="M",
    )


def _attach_request_state(request, staff_user):
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)

    request.user = staff_user
    return request


@pytest.mark.django_db
def test_announcement_admin_resend_emails(
    monkeypatch, rf, admin_site, staff_user, announcement, user
):
    ua = UserAnnouncement.objects.create(user=user, announcement=announcement)

    sent = []

    def fake_send(instance, *, force=False):
        sent.append((instance.pk, force))
        return True

    monkeypatch.setattr("announcement.admin.send_user_announcement_email", fake_send)

    model_admin = AnnouncementAdmin(Announcement, admin_site)

    request = _attach_request_state(rf.post("/admin/announcement/announcement/"), staff_user)

    queryset = Announcement.objects.filter(pk=announcement.pk)
    model_admin.resend_emails(request, queryset)

    assert sent == [(ua.pk, True)]


@pytest.mark.django_db
def test_user_announcement_admin_send_selected(
    monkeypatch, rf, admin_site, staff_user, announcement, user
):
    ua = UserAnnouncement.objects.create(user=user, announcement=announcement)

    calls = []

    def fake_send(instance, *, force=False):
        calls.append((instance.pk, force))
        return not instance.email_sent_at

    monkeypatch.setattr("announcement.admin.send_user_announcement_email", fake_send)

    model_admin = UserAnnouncementAdmin(UserAnnouncement, admin_site)
    request = _attach_request_state(rf.post("/admin/announcement/userannouncement/"), staff_user)

    queryset = UserAnnouncement.objects.filter(pk=ua.pk)
    model_admin.send_selected(request, queryset)

    assert calls == [(ua.pk, False)]


@pytest.mark.django_db
def test_user_announcement_admin_force_resend(
    monkeypatch, rf, admin_site, staff_user, announcement, user
):
    ua = UserAnnouncement.objects.create(user=user, announcement=announcement)

    calls = []

    def fake_send(instance, *, force=False):
        calls.append((instance.pk, force))
        return True

    monkeypatch.setattr("announcement.admin.send_user_announcement_email", fake_send)

    model_admin = UserAnnouncementAdmin(UserAnnouncement, admin_site)
    request = _attach_request_state(rf.post("/admin/announcement/userannouncement/"), staff_user)

    queryset = UserAnnouncement.objects.filter(pk=ua.pk)
    model_admin.force_resend_selected(request, queryset)

    assert calls == [(ua.pk, True)]
