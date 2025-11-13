import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from accounts.permissions import HasPaid, HasPurchased, IsVerified, ProfileCompleted
from payments.models import Transaction


User = get_user_model()


@pytest.fixture
def request_factory():
    return APIRequestFactory()


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(email="verified@example.com", password="secret")
    user.is_verified = True
    user.profile_completed = True
    user.has_paid = True
    user.save()
    return user


@pytest.mark.django_db
def test_is_verified_permission_allows_verified_user(request_factory, verified_user):
    request = request_factory.get("/test")
    request.user = verified_user

    assert IsVerified().has_permission(request, view=None) is True


@pytest.mark.django_db
def test_is_verified_permission_blocks_unverified_user(request_factory):
    user = User.objects.create_user(email="plain@example.com", password="secret")
    request = request_factory.get("/test")
    request.user = user

    assert IsVerified().has_permission(request, view=None) is False


@pytest.mark.django_db
def test_profile_completed_permission_requires_completed_profile(request_factory, verified_user):
    request = request_factory.get("/test")
    request.user = verified_user

    assert ProfileCompleted().has_permission(request, view=None) is True

    verified_user.profile_completed = False
    verified_user.save(update_fields=["profile_completed"])

    request.user = verified_user
    assert ProfileCompleted().has_permission(request, view=None) is False


@pytest.mark.django_db
def test_has_paid_permission_requires_payment_flag(request_factory, verified_user):
    request = request_factory.get("/test")
    request.user = verified_user

    assert HasPaid().has_permission(request, view=None) is True

    verified_user.has_paid = False
    verified_user.save(update_fields=["has_paid"])
    request.user = verified_user

    assert HasPaid().has_permission(request, view=None) is False


@pytest.mark.django_db
def test_has_purchased_permission_matches_transactions(request_factory, verified_user):
    GamePassPermission = HasPurchased("game-pass")
    perm = GamePassPermission()

    request = request_factory.get("/test")
    request.user = verified_user

    # transaction with matching item
    Transaction.objects.create(
        user=verified_user,
        amount=1000,
        status="completed",
        items=json.dumps(["game-pass", "other"]),
        track_id="track1",
        order_id="order1",
    )

    assert perm.has_permission(request, view=None) is True


@pytest.mark.django_db
def test_has_purchased_permission_handles_non_matching_and_bad_data(request_factory, verified_user):
    OtherPermClass = HasPurchased("vip")
    perm = OtherPermClass()

    request = request_factory.get("/test")
    request.user = verified_user

    # Non matching transaction
    Transaction.objects.create(
        user=verified_user,
        amount=2000,
        status="completed",
        items=json.dumps(["basic"]),
        track_id="track2",
        order_id="order2",
    )

    # Invalid JSON should be ignored
    Transaction.objects.create(
        user=verified_user,
        amount=1500,
        status="completed",
        items="not-json",
        track_id="track3",
        order_id="order3",
    )

    assert perm.has_permission(request, view=None) is False
