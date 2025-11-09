import logging
import random
import string

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LobbygameResult
from .serializers import LobbygameResultSerializer
from payments.models import DiscountCode

logger = logging.getLogger(__name__)


class LobbygameStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result, _ = LobbygameResult.objects.get_or_create(
            request_uuid="status", defaults={"description": "not started"}
        )
        serializer = LobbygameResultSerializer(result)
        return Response({"status": serializer.data}, status=status.HTTP_200_OK)


class LobbygameGetDiscount(APIView):
    """
    Fetch discount info by requestUuid (from URL path)
    """

    permission_classes = [AllowAny]

    def get(self, request, uuid):
        result = get_object_or_404(LobbygameResult, request_uuid=uuid)
        serializer = LobbygameResultSerializer(result)
        return Response({"status": serializer.data}, status=status.HTTP_200_OK)


class LobbygameCreateDiscountView(APIView):
    """
    Create discount coupons with limited rewards:
      - First 5: 100%
      - Next 10: 50%
      - After that: no coupon, status says "max reached"
    """

    permission_classes = [AllowAny]

    def post(self, request, uuid):
        existing = LobbygameResult.get_or_none(uuid)
        if existing:
            serializer = LobbygameResultSerializer(existing)
            return Response(
                {
                    "success": True,
                    "request_uuid": uuid,
                    "discount_percentage": existing.discount_percentage or 0,
                    "message": existing.description,
                    "coupon_code": existing.coupon_code,
                    "status": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        winners_count = (
            LobbygameResult.objects.exclude(request_uuid="status").count()
        )

        if winners_count < 5:
            discount_percentage = 100
            message = "Congratulations! You are among the first 5 winners! Enjoy 100% discount!"
        elif winners_count < 15:
            discount_percentage = 50
            message = "You’ve won a 50% discount code!"
        else:
            discount_percentage = 0
            message = "We have reached the maximum number of winners! Hope to see you around."

        coupon_code_str = None
        if discount_percentage > 0:
            coupon_code_str = self.generate_coupon_code()
            DiscountCode.objects.create(
                code=coupon_code_str,
                percentage=discount_percentage,
                target="gamejam",
                max_uses=1,
                current_uses=0,
            )

        result = LobbygameResult.objects.create(
            request_uuid=uuid,
            discount_percentage=discount_percentage or None,
            coupon_code=coupon_code_str,
            description=message,
        )

        serializer = LobbygameResultSerializer(result)

        return Response(
            {
                "success": True,
                "request_uuid": uuid,
                "discount_percentage": discount_percentage,
                "message": message,
                "coupon_code": coupon_code_str,
                "status": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def generate_coupon_code(self):
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not DiscountCode.objects.filter(code=code).exists():
                return code
