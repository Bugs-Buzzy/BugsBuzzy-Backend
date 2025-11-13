from rest_framework.test import APIRequestFactory

from accounts.throttling import CheckEmailThrottle


def test_get_ident_prefers_forwarded_header():
    factory = APIRequestFactory()
    request = factory.post("/check-email", HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2")

    throttle = CheckEmailThrottle()

    assert throttle.get_ident(request) == "1.1.1.1"


def test_get_ident_falls_back_to_remote_addr():
    factory = APIRequestFactory()
    request = factory.post("/check-email")
    request.META["REMOTE_ADDR"] = "3.3.3.3"

    throttle = CheckEmailThrottle()

    assert throttle.get_ident(request) == "3.3.3.3"


def test_get_cache_key_uses_scope_and_ident():
    factory = APIRequestFactory()
    request = factory.post("/check-email", HTTP_X_FORWARDED_FOR="9.9.9.9")

    throttle = CheckEmailThrottle()
    key = throttle.get_cache_key(request, view=None)

    assert key.endswith("9.9.9.9")
    assert "check_email" in key
