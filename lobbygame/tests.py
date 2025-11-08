from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from lobbygame.models import LobbygameResult
from payments.models import DiscountCode

User = get_user_model()


@override_settings(
    APPEND_SLASH=False,
    DEBUG=True,
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=None,
)
class LobbygameAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", is_verified=True
        )

    def test_lobbygame_status_entry_exists(self):
        """Verify the initial status row exists"""
        result = LobbygameResult.objects.get(request_uuid="status")
        self.assertEqual(result.description, "not started")

    def test_lobbygame_get_status(self):
        """GET /lobbygame/status/ returns correct status"""
        response = self.client.get("/lobbygame/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"]["description"], "not started")

    def test_lobbygame_get_discount_with_uuid(self):
        """GET /lobbygame/discount-code/with-request-uuid/<uuid>/"""
        result = LobbygameResult.objects.first()
        response = self.client.get(f"/lobbygame/discount-code/with-request-uuid/{result.request_uuid}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)

    def test_create_discount_first_five_users(self):
        """First five requests should get 100%"""
        for i in range(5):
            uuid = f"req-{i}"
            response = self.client.post(f"/lobbygame/discount-code/{uuid}/")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            code = DiscountCode.objects.get(code=response.data["coupon_code"])
            self.assertEqual(code.percentage, 100)

    def test_create_discount_next_ten_users(self):
        """Next ten requests get 50%"""
        for i in range(5):
            LobbygameResult.objects.create(request_uuid=f"pre{i}", discount_percentage=100)
        for i in range(5, 15):
            uuid = f"req-{i}"
            response = self.client.post(f"/lobbygame/discount-code/{uuid}/")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            code = DiscountCode.objects.get(code=response.data["coupon_code"])
            self.assertEqual(code.percentage, 50)

    def test_create_discount_after_limit(self):
        """After 15 total requests, no new codes generated"""
        for i in range(15):
            LobbygameResult.objects.create(request_uuid=f"r{i}", discount_percentage=50)
        response = self.client.post("/lobbygame/discount-code/req-16/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("maximum number of winners", response.data["message"])
