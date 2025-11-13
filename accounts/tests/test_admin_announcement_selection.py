import pytest
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from accounts.admin import CustomUserAdmin


User = get_user_model()


class DummyMessages(list):
    def add(self, level, message, extra_tags="", fail_silently=False):
        self.append((level, message))


class DummySession(dict):
    @property
    def modified(self):
        return self.get("__modified", False)

    @modified.setter
    def modified(self, value):
        self["__modified"] = value


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(email="admin@example.com", password="pass1234")
    return user


def build_request(user, method="post", path="admin:accounts_user_changelist", data=None):
    factory = RequestFactory()
    req_method = getattr(factory, method.lower())
    request = req_method(reverse(path), data=data or {})
    request.user = user
    request._messages = DummyMessages()
    request.session = DummySession()
    return request


def build_admin_request(path, method="get", data=None):
    factory = RequestFactory()
    req_method = getattr(factory, method.lower())
    return req_method(path, data=data or {})


@pytest.mark.django_db
def test_selection_token_persists_more_than_limit(admin_user):
    users = User.objects.bulk_create(
        [
            User(email=f"user{i}@example.com", normalized_email=f"user{i}@example.com", password="!")
            for i in range(150)
        ]
    )

    request = build_request(
        admin_user,
        data={
            "action": "create_announcement_for_selected",
            "_selected_action": [str(user.pk) for user in users],
            "select_across": "1",
        },
    )

    user_admin = CustomUserAdmin(User, django_admin.site)
    selected_queryset = User.objects.filter(pk__in=[user.pk for user in users])
    response = user_admin.create_announcement_for_selected(request, selected_queryset)

    assert response.status_code == 302
    assert "token=" in response.url

    token = response.url.split("token=")[1]
    session_key = f"announcement_selection_{token}"
    assert session_key in request.session
    assert len(request.session[session_key]) == 150
    assert request.session.modified is True

@pytest.mark.django_db
def test_create_announcement_view_uses_session_ids(admin_user):
    users = User.objects.bulk_create(
        [
            User(email=f"user{i}@example.com", normalized_email=f"user{i}@example.com", password="!")
            for i in range(105)
        ]
    )

    user_admin = CustomUserAdmin(User, django_admin.site)

    token = "tok123"
    session_key = f"announcement_selection_{token}"
    session = DummySession()
    session[session_key] = [user.pk for user in users]
    session.modified = False

    path = f"/admin/accounts/user/create_announcement/?token={token}"
    request = build_admin_request(path)
    request.user = admin_user
    request._messages = DummyMessages()
    request.session = session

    response = user_admin.create_announcement_view(request)

    assert response.status_code == 200
    context = response.context_data
    assert context["users_count"] == 105
    assert len(context["sample_users"]) == 10
    assert context["selection_token"] == token
    assert context["raw_ids"] is None

    form_post_data = {
        "token": token,
        "existing_announcement": "",
        "title": "Announcement",
        "description": "Body",
    }
    post_request = build_admin_request(path, method="post", data=form_post_data)
    post_request.user = admin_user
    post_request._messages = DummyMessages()
    post_request.session = session

    response_post = user_admin.create_announcement_view(post_request)

    assert response_post.status_code == 302
    assert session_key not in post_request.session
    assert post_request.session.modified is True
