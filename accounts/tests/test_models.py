import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_without_email_raises():
    with pytest.raises(ValueError):
        User.objects.create_user(email=None, password="secret")


@pytest.mark.django_db
def test_create_user_sets_normalized_email_when_missing():
    user = User.objects.create_user(email="User@Example.com", password="pass1234")

    assert user.normalized_email == "user@example.com"


@pytest.mark.django_db
def test_create_user_respects_provided_normalized_email():
    user = User.objects.create_user(
        email="User@Example.com",
        password="pass1234",
        normalized_email="custom@example.com",
    )

    assert user.normalized_email == "custom@example.com"


@pytest.mark.django_db
def test_create_superuser_requires_is_staff():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            is_staff=False,
        )


@pytest.mark.django_db
def test_create_superuser_requires_is_superuser():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            is_superuser=False,
        )


@pytest.mark.django_db
def test_user_str_returns_email():
    user = User.objects.create_user(email="someone@example.com", password="pass1234")

    assert str(user) == "someone@example.com"
