import logging
import random
import string
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import LobbygameResult, LobbyGameStatus
from .serializers import LobbygameSubmissionSerializer, LobbygameResultSerializer
from payments.models import DiscountCode

logger = logging.getLogger(__name__)


class LobbygameStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            result = LobbygameResult.get_description("status")
            serializer = LobbygameResultSerializer(result)
            return Response({"description": serializer.data}, status=status.HTTP_200_OK)
        except LobbygameResult.DoesNotExist:
            return Response(
                {"message": "exception occurred!"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LobbygameGetDiscount(APIView):
    """
    Fetch discount info by requestUuid (from URL path)
    """

    permission_classes = [AllowAny]

    def get(self, request, uuid):
        try:
            result = LobbygameResult.get_description(uuid)
            serializer = LobbygameResultSerializer(result)
            return Response({"description": serializer.data}, status=status.HTTP_200_OK)
        except LobbygameResult.DoesNotExist:
            return Response(
                {"message": "exception occurred!"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LobbygameCreateDiscountView(APIView):
    """
    Create discount coupons with limited rewards:
      - First 5: 100%
      - Next 10: 50%
      - After that: no coupon, status says "max reached"
    """

    permission_classes = [AllowAny]

    def post(self, request):
        user = request.user
        request_uuid = request.data.get("request_uuid")

        if not request_uuid:
            return Response(
                {"error": "Missing 'request_uuid' in request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Count total existing winners
        total_created = LobbyGameStatus.objects.count()

        if total_created < 6:
            discount_percentage = 100
            message = "Congratulations! You are among the first 5 winners! Enjoy 100% discount!"
        elif total_created < 16:
            discount_percentage = 50
            message = "You’ve won a 50% discount code!"
        else:
            discount_percentage = 0
            message = "We have reached the maximum number of winners! Hope to see you around."

        # If we still give a discount, generate a code
        coupon_code_str = None
        discount_code = None

        if discount_percentage > 0:
            coupon_code_str = self.generate_coupon_code()
            discount_code = DiscountCode.objects.create(
                code=coupon_code_str,
                percentage=discount_percentage,
                target="gamejam",
                max_uses=1,
                current_uses=0,
            )

        # Save record in LobbyGameStatus
        LobbyGameStatus.objects.create(
            request_uuid=request_uuid,
            description=coupon_code_str or message,
        )

        # Response output
        return Response(
            {
                "success": True,
                "request_uuid": request_uuid,
                "discount_percentage": discount_percentage,
                "message": message,
                "coupon_code": coupon_code_str,
            },
            status=status.HTTP_201_CREATED,
        )

    def generate_coupon_code(self):
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not DiscountCode.objects.filter(code=code).exists():
                return code
