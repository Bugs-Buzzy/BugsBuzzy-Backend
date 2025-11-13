import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from accounts.admin import CustomUserAdmin
from accounts.models import User
from announcement.models import Announcement, UserAnnouncement


def _prepare_request(request, user):
    """Attach session and message storage to mimic admin requests."""

    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    # Django's admin uses the messages framework; attach fallback storage
    messages_storage = FallbackStorage(request)
    setattr(request, "_messages", messages_storage)

    request.user = user
    return request


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="strong-pass-123",
        national_code="1234567890",
        phone_number="09100000000",
        gender="M",
    )


@pytest.mark.django_db
def test_create_announcement_action_stores_all_selected_users(admin_site, rf, superuser):
    model_admin = CustomUserAdmin(User, admin_site)

    users = [
        User.objects.create_user(
            email=f"member{i}@example.com",
            password="pass1234",
            national_code=f"{i:010d}",
            phone_number=f"091{i:08d}",
            gender="M",
        )
        for i in range(1, 151)
    ]

    request = rf.post("/admin/accounts/user/", {"action": "create_announcement_for_selected"})
    _prepare_request(request, superuser)

    queryset = User.objects.filter(id__in=[user.id for user in users])

    response = model_admin.create_announcement_for_selected(request, queryset)

    assert response.status_code == 302
    parsed = urlparse(response["Location"])
    token = parse_qs(parsed.query).get("token", [None])[0]
    assert token is not None

    session_key = f"announcement_selection_{token}"
    assert session_key in request.session
    stored_ids = request.session[session_key]
    assert len(stored_ids) == len(users)
    assert set(stored_ids) == {user.id for user in users}


@pytest.mark.django_db(transaction=True)
def test_create_announcement_view_creates_links_and_clears_session(admin_site, rf, superuser, monkeypatch):
    model_admin = CustomUserAdmin(User, admin_site)

    users = [
        User.objects.create_user(
            email=f"participant{i}@example.com",
            password="pass1234",
            national_code=f"{i+200:010d}",
            phone_number=f"092{i:08d}",
            gender="F",
        )
        for i in range(1, 6)
    ]

    token = uuid.uuid4().hex

    request = rf.post(
        "/admin/accounts/user/create_announcement/",
        {
            "token": token,
            "title": "اطلاعیه مهم",
            "description": "**سلام** دوستان!",
        },
    )
    _prepare_request(request, superuser)

    session_key = f"announcement_selection_{token}"
    request.session[session_key] = [user.id for user in users]
    request.session.save()

    # Prevent sending real emails during the test
    monkeypatch.setattr(
        "announcement.signals.send_user_announcement_email",
        lambda instance, force=False: True,
    )

    assert Announcement.objects.count() == 0
    assert UserAnnouncement.objects.count() == 0

    response = model_admin.create_announcement_view(request)

    assert response.status_code == 302
    assert Announcement.objects.filter(title="اطلاعیه مهم").count() == 1
    announcement = Announcement.objects.get(title="اطلاعیه مهم")
    assert announcement.description == "**سلام** دوستان!"
    assert UserAnnouncement.objects.filter(announcement=announcement).count() == len(users)

    # Session token should be cleared after successful handling
    assert session_key not in request.session
