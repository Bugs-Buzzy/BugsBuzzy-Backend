import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

User = get_user_model()


@override_settings(
    APPEND_SLASH=False,
    DEBUG=True,
    SECURE_SSL_REDIRECT=False,
    SECURE_PROXY_SSL_HEADER=None,
)
class NewAuthFlowTestCase(APITestCase):
    """Test new authentication flow (send-code → verify-code)"""

    def setUp(self):
        self.client = APIClient()
        self.send_code_url = reverse("send_code")
        self.verify_code_url = reverse("verify_code")
        self.login_url = reverse("login")
        self.profile_url = reverse("profile")
        self.forgot_password_url = reverse("forgot_password")
        self.change_password_url = reverse("change_password")
        self.refresh_url = reverse("token_refresh")

        # داده‌های تست با validation صحیح
        self.valid_profile_data = {
            "email": "test@example.com",
            "first_name": "علی",  # فارسی
            "last_name": "احمدی",  # فارسی
            "national_code": "1234567891",  # کد ملی معتبر
            "phone_number": "09123456789",
            "gender": "M",
            "city": "تهران",
        }

    @patch("accounts.views.send_verification_email")
    def test_send_code_new_user(self, mock_send_email):
        """تست ارسال کد برای کاربر جدید"""
        mock_send_email.return_value = True

        response = self.client.post(
            self.send_code_url, {"email": "newuser@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertTrue(response.data["is_new_user"])

        # بررسی کاربر ساخته شده
        user = User.objects.get(email="newuser@example.com")
        self.assertIsNotNone(user.verification_code)
        self.assertFalse(user.has_usable_password())  # رمز unusable
        mock_send_email.assert_called_once()

    @patch("accounts.views.send_verification_email")
    def test_send_code_existing_user(self, mock_send_email):
        """تست ارسال کد برای کاربر موجود"""
        mock_send_email.return_value = True

        # ساخت کاربر
        user = User.objects.create_user(email="test@example.com")
        user.set_password("TestPass123")
        user.save()

        response = self.client.post(
            self.send_code_url, {"email": "test@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_new_user"])

    @patch("accounts.views.send_verification_email")
    def test_code_reuse_within_15_minutes(self, mock_send_email):
        """تست استفاده مجدد از همان کد در 15 دقیقه"""
        mock_send_email.return_value = True

        # ساخت کاربر با کد
        user = User.objects.create_user(email="test@example.com")
        user.verification_code = 123456
        user.code_updated_at = timezone.now()
        user.try_count = 0
        user.save()

        old_code = user.verification_code

        # ارسال مجدد
        response = self.client.post(
            self.send_code_url, {"email": "test@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # کد نباید تغییر کرده باشد
        user.refresh_from_db()
        self.assertEqual(user.verification_code, old_code)
        self.assertEqual(user.try_count, 1)

    @patch("accounts.views.send_verification_email")
    def test_code_regeneration_after_15_minutes(self, mock_send_email):
        """تست تولید کد جدید بعد از 15 دقیقه"""
        mock_send_email.return_value = True

        # کاربر با کد منقضی شده
        user = User.objects.create_user(email="test@example.com")
        user.verification_code = 111111
        user.code_updated_at = timezone.now() - timedelta(minutes=20)
        user.try_count = 3
        user.save()

        old_code = user.verification_code

        response = self.client.post(
            self.send_code_url, {"email": "test@example.com"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # کد باید تغییر کرده باشد
        user.refresh_from_db()
        self.assertNotEqual(user.verification_code, old_code)
        self.assertEqual(user.try_count, 1)  # reset

    def test_verify_code_success(self):
        """تست تایید کد موفق"""
        # ساخت کاربر با کد
        user = User.objects.create_user(email="test@example.com")
        user.verification_code = 123456
        user.code_updated_at = timezone.now()
        user.save()

        response = self.client.post(
            self.verify_code_url,
            {"email": "test@example.com", "verification_code": "123456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

        # کاربر باید verified شده باشد
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertEqual(user.status, "verified")

    def test_login_with_password(self):
        """تست ورود با رمز عبور"""
        user = User.objects.create_user(email="test@example.com")
        user.set_password("TestPass123")
        user.is_verified = True
        user.save()

        response = self.client.post(
            self.login_url,
            {"email": "test@example.com", "password": "TestPass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    @patch("accounts.views.send_verification_email")
    def test_forgot_password_flow(self, mock_send_email):
        """تست فلوی فراموشی رمز"""
        mock_send_email.return_value = True

        # ساخت کاربر با رمز
        user = User.objects.create_user(email="test@example.com")
        user.set_password("OldPass123")
        user.save()

        self.assertTrue(user.has_usable_password())

        # ارسال کد
        self.client.post(self.send_code_url, {"email": "test@example.com"}, format="json")

        user.refresh_from_db()
        code = user.verification_code

        # بازنشانی رمز
        response = self.client.post(
            self.forgot_password_url,
            {"email": "test@example.com", "verification_code": str(code)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        # رمز باید unusable شده باشد
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_verified)

    def test_profile_update_with_valid_data(self):
        """تست آپدیت پروفایل با داده معتبر"""
        user = User.objects.create_user(email="test@example.com")
        user.is_verified = True
        user.national_code = "1234567891"
        user.phone_number = "09123456789"
        user.save()

        # Token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        update_data = {
            "first_name": "علی",
            "last_name": "احمدی",
            "phone_number": "09123456789",
            "national_code": "1234567891",
            "gender": "M",
            "city": "تهران",
        }

        response = self.client.put(self.profile_url, update_data, format="json")

        if response.status_code != status.HTTP_200_OK:
            print(f"Response: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.profile_completed)

    def test_profile_update_invalid_persian_name(self):
        """تست رد کردن نام غیرفارسی"""
        user = User.objects.create_user(email="test@example.com")
        user.is_verified = True
        user.national_code = "1234567891"
        user.phone_number = "09123456789"
        user.save()

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        update_data = {
            "first_name": "John",  # انگلیسی - باید رد بشه
            "last_name": "Doe",
            "phone_number": "09123456789",
            "national_code": "1234567891",
            "gender": "M",
            "city": "Tehran",
        }

        response = self.client.put(self.profile_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("first_name", response.data)

    def test_change_password_new_user(self):
        """تست تنظیم رمز برای کاربر جدید"""
        user = User.objects.create_user(email="test@example.com")
        user.is_verified = True
        user.set_unusable_password()
        user.save()

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = self.client.post(
            self.change_password_url, {"new_password": "NewPass123"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password("NewPass123"))

    def test_change_password_existing_user(self):
        """تست تغییر رمز برای کاربر موجود"""
        user = User.objects.create_user(email="test@example.com")
        user.set_password("OldPass123")
        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = self.client.post(
            self.change_password_url,
            {"current_password": "OldPass123", "new_password": "NewPass456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPass456"))
        self.assertFalse(user.check_password("OldPass123"))
