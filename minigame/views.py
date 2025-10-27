import logging
import random
import string
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import MinigameResult
from .serializers import MinigameSubmissionSerializer, MinigameResultSerializer
from payments.models import DiscountCode

logger = logging.getLogger(__name__)


def calculate_discount_percentage(carrot_count: int, coin_count: int) -> int:
    """
    Calculate discount percentage using probabilistic distribution.
    
    Target distribution:
    - ~70% chance: discount < 30%
    - ~95% chance: discount <= 35%
    - 100% chance: discount <= 40% (hard cap)
    
    The carrot and coin counts influence the parameters of the distribution:
    - Higher scores shift the mean upward
    - But the randomness ensures variety and prevents exploitation
    """
    # Normalize scores to 0-1 range
    # Max realistic: carrot=200, coin=15
    carrot_normalized = min(carrot_count / 200, 1.0)
    coin_normalized = min(coin_count / 15, 1.0)
    
    # Combined performance score (0-1)
    performance = (carrot_normalized * 0.4 + coin_normalized * 0.6)
    
    # Base mean varies from 15% to 23% based on performance
    base_mean = 15 + (performance * 8)
    
    # Use beta distribution for controlled randomness
    # Alpha and beta parameters control the shape
    # Higher performance = slightly higher variance (more chance for high rewards)
    alpha = 3.5 + (performance * 1.0)  # 3.5-4.5 range
    beta = 9.0 - (performance * 2.0)   # 7.0-9.0 range
    
    # Generate random value from beta distribution (0-1)
    random_factor = np.random.beta(alpha, beta)
    
    # Scale to discount range with cap at 40
    # Allows reaching up to 40% for excellent performance with luck
    discount = base_mean + (random_factor * 17)
    
    # Apply hard cap at 40% and floor at 5%
    discount = max(5, min(40, int(discount)))
    
    return discount


class MinigameStatusView(APIView):
    """
    Check if user has already played the minigame
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            result = MinigameResult.objects.get(user=user)
            serializer = MinigameResultSerializer(result)
            return Response(
                {"has_played": True, "result": serializer.data}, status=status.HTTP_200_OK
            )
        except MinigameResult.DoesNotExist:
            return Response(
                {
                    "has_played": False,
                    "message": "You can play the minigame once to earn a discount coupon!",
                },
                status=status.HTTP_200_OK,
            )


class MinigameSubmitView(APIView):
    """
    Submit minigame results and generate coupon
    Each user can only play once
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if user has already played
        if MinigameResult.objects.filter(user=user).exists():
            return Response(
                {"error": "You have already played the minigame. Each user can only play once."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MinigameSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        carrot_count = serializer.validated_data["carrot_count"]
        coin_count = serializer.validated_data["coin_count"]

        # Anti-cheat: If scores are suspiciously high, apply penalty
        if carrot_count > 300 or coin_count > 20:
            discount_percentage = -20  # 20% penalty (increases price)
            logger.warning(
                f"User {user.email} submitted suspicious minigame scores: "
                f"carrot={carrot_count}, coin={coin_count}"
            )
        else:
            # Calculate discount using probabilistic formula
            discount_percentage = calculate_discount_percentage(carrot_count, coin_count)

        # Generate unique coupon code
        coupon_code_str = self.generate_coupon_code()

        # Create discount code
        discount_code = DiscountCode.objects.create(
            code=coupon_code_str,
            percentage=discount_percentage,
            target="gamejam",
            max_uses=1,  # Single use only
            current_uses=0,
        )

        # Create minigame result
        result = MinigameResult.objects.create(
            user=user,
            carrot_count=carrot_count,
            coin_count=coin_count,
            discount_percentage=discount_percentage,
            coupon_code=discount_code,
        )

        logger.info(
            f"User {user.email} completed minigame: "
            f"carrot={carrot_count}, coin={coin_count}, "
            f"discount={discount_percentage}%, code={coupon_code_str}"
        )

        serializer = MinigameResultSerializer(result)
        return Response(
            {
                "success": True,
                "message": "Congratulations! Your discount coupon has been generated.",
                "result": serializer.data,
                "coupon_code": coupon_code_str,
                "discount_percentage": discount_percentage,
            },
            status=status.HTTP_201_CREATED,
        )

    def generate_coupon_code(self):
        """Generate a unique 8-character coupon code"""
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not DiscountCode.objects.filter(code=code).exists():
                return code
