from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import MinigameResult
from payments.models import DiscountCode

User = get_user_model()


class MinigameAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", is_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_minigame_status_not_played(self):
        """Test status endpoint when user hasn't played"""
        response = self.client.get("/minigame/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_played"])

    def test_minigame_submit_valid(self):
        """Test submitting valid game results"""
        response = self.client.post(
            "/minigame/submit/", {"carrot_count": 100, "coin_count": 5}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        
        # With probabilistic calculation, discount should be in reasonable range
        discount = response.data["discount_percentage"]
        self.assertGreaterEqual(discount, 5)   # Minimum possible
        self.assertLessEqual(discount, 40)     # Maximum possible
        self.assertGreaterEqual(discount, 18)  # For this score, should be >= 18
        self.assertLessEqual(discount, 34)     # For this score, should be <= 34

        # Verify result is saved
        result = MinigameResult.objects.get(user=self.user)
        self.assertEqual(result.carrot_count, 100)
        self.assertEqual(result.coin_count, 5)
        self.assertEqual(result.discount_percentage, discount)

        # Verify coupon code is created
        self.assertIsNotNone(result.coupon_code)
        self.assertEqual(result.coupon_code.percentage, discount)
        self.assertEqual(result.coupon_code.max_uses, 1)

    def test_minigame_submit_already_played(self):
        """Test that user can only play once"""
        # First play
        self.client.post("/minigame/submit/", {"carrot_count": 100, "coin_count": 5})

        # Second play should fail
        response = self.client.post("/minigame/submit/", {"carrot_count": 200, "coin_count": 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already played", response.data["error"])

    def test_minigame_submit_invalid_scores(self):
        """Test anti-cheat for invalid scores"""
        response = self.client.post(
            "/minigame/submit/", {"carrot_count": 500, "coin_count": 30}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_minigame_status_after_playing(self):
        """Test status endpoint after playing"""
        self.client.post("/minigame/submit/", {"carrot_count": 100, "coin_count": 5})

        response = self.client.get("/minigame/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_played"])
        self.assertIn("result", response.data)

    def test_discount_calculation(self):
        """Test discount calculation ranges for various scores"""
        test_cases = [
            (0, 0, 15, 29),      # Worst: 15-29% range
            (100, 5, 18, 34),    # Average: 18-34% range
            (200, 10, 20, 36),   # Good: 20-36% range
            (150, 8, 19, 35),    # Above average: 19-35% range
            (200, 15, 23, 37),   # Excellent: 23-37% range
        ]

        for carrot, coin, min_expected, max_expected in test_cases:
            with self.subTest(carrot=carrot, coin=coin):
                user = User.objects.create_user(
                    email=f"test_{carrot}_{coin}@example.com",
                    password="testpass123",
                    is_verified=True,
                )
                client = APIClient()
                client.force_authenticate(user=user)

                response = client.post("/minigame/submit/", {"carrot_count": carrot, "coin_count": coin})
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                
                discount = response.data["discount_percentage"]
                self.assertGreaterEqual(discount, min_expected, 
                    f"Discount {discount}% is less than expected minimum {min_expected}%")
                self.assertLessEqual(discount, max_expected,
                    f"Discount {discount}% is more than expected maximum {max_expected}%")
