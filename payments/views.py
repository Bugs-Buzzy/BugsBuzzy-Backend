import requests
import random
import json
import logging
from datetime import datetime
from django.shortcuts import redirect
from django.db.models import F
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsVerified, ProfileCompleted
from django.conf import settings
from .models import Transaction, DiscountCode
from .utils import calculate_amount, apply_purchase
from .throttling import PriceCheckThrottle
from django.apps import apps

logger = logging.getLogger(__name__)


class PurchasedItemsView(APIView):
    """
    Get list of items that user has already purchased.
    Used to prevent duplicate purchases and show purchase history.
    """

    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def get(self, request):
        user = request.user

        # Get all completed transactions for this user
        completed_transactions = Transaction.objects.filter(user=user, status="completed").order_by(
            "-completed_at"
        )

        # Extract all purchased items
        purchased_items = []
        for transaction in completed_transactions:
            try:
                items = json.loads(transaction.items)
                purchased_items.extend(items)
            except (json.JSONDecodeError, TypeError):
                continue

        # Remove duplicates while preserving order
        unique_items = []
        seen = set()
        for item in purchased_items:
            if item not in seen:
                unique_items.append(item)
                seen.add(item)

        return Response(
            {
                "purchased_items": unique_items,
                "total_transactions": completed_transactions.count(),
                "total_spent": sum(t.amount for t in completed_transactions),
            },
            status=status.HTTP_200_OK,
        )


class PriceView(APIView):
    """
    Calculate price for items WITHOUT discount code.
    This endpoint has no rate limiting as it's used for real-time price updates.
    """

    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def get(self, request):
        items = request.query_params.getlist("items")

        if len(items) == 0:
            return Response({"error": "Items are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate amount without discount
        amount, _, _ = calculate_amount(items, None)

        return Response(
            {"amount": int(amount)},
            status=status.HTTP_200_OK,
        )


class DiscountView(APIView):
    """
    Validate discount code and calculate discounted price.
    This endpoint has STRICT rate limiting to prevent brute-force attacks.
    """

    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]
    throttle_classes = [PriceCheckThrottle]

    def get(self, request):
        discount_code = request.query_params.get("code", "").strip()
        items = request.query_params.getlist("items")

        if len(items) == 0:
            return Response({"error": "Items are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not discount_code:
            return Response(
                {"error": "Discount code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Find discount code (case-insensitive)
        discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()

        if not discount:
            return Response(
                {"error": "Invalid discount code", "discount_applied": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not discount.is_valid():
            return Response(
                {"error": "Discount code has reached its usage limit", "discount_applied": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate amount with discount
        amount, applied, not_available = calculate_amount(items, discount)

        if len(not_available) > 0:
            return Response(
                {"Unavailable items": ",".join(not_available)},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        return Response(
            {
                "amount": int(amount),
                "discount_applied": applied,
                "discount_percentage": discount.percentage if applied else 0,
            },
            status=status.HTTP_200_OK,
        )


class PaymentView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def post(self, request):
        user = request.user
        discount_code = request.data.get("discount_code", "").strip()
        items = request.data.get("items", [])

        if len(items) == 0:
            return Response({"error": "Items are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate discount code if provided
        discount = None
        if discount_code:
            discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()

            if not discount:
                return Response(
                    {"error": "Invalid discount code"}, status=status.HTTP_400_BAD_REQUEST
                )

            if not discount.is_valid():
                return Response(
                    {"error": "Discount code has reached its usage limit"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        amount, _, not_available = calculate_amount(items, discount)
        order_id = random.randint(100000, 999999)

        if len(not_available) > 0:
            return Response(
                {"Unavailable items": ",".join(not_available)},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        try:
            response = requests.post(
                "https://gateway.zibal.ir/request/lazy",
                json={
                    "merchant": settings.MERCHANT_ID,
                    "amount": int(amount),
                    "callbackUrl": settings.PAYMENT_CALLBACK_URL,
                    "description": "BugsBuzzy Payment\n" + json.dumps(items),
                    "orderId": str(order_id),
                    "mobile": user.phone_number,
                    "checkMobileWithCard": False,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Zibal gateway error: {str(e)}")
            return Response(
                {"error": "Gateway connection failed"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.error(f"Unexpected payment error: {str(e)}")
            return Response(
                {"error": "Unexpected payment error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if "result" in data and data["result"] == 100:
            transaction = Transaction.objects.create(
                track_id=str(data["trackId"]),
                order_id=str(order_id),
                user=user,
                items=json.dumps(items),
                amount=int(amount),
                discount=discount,
                gateway_response=data.get("message", ""),
                result=int(data["result"]),
            )
            return Response(
                {"redirect_url": f"https://gateway.zibal.ir/start/{data['trackId']}"}, status=200
            )
        else:
            logger.warning(f"Zibal returned error: {data}")
            error_message = data.get("message", "Unknown gateway error")
            return Response(
                {"error": f"Gateway error: {error_message}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class CallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        transaction = Transaction.objects.filter(track_id=data["trackId"]).first()
        if not transaction:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = requests.post(
            "https://gateway.zibal.ir/verify",
            json={"merchant": settings.MERCHANT_ID, "trackId": int(data["trackId"])},
            timeout=10,
        )

        result = response.json()
        if "status" not in result.keys():
            transaction.status = "failed"
            transaction.gateway_response = result.get("message", "")
            transaction.save()
            return redirect(settings.PAYMENT_FAILED_URL)

        if transaction.order_id == str(result["orderId"]) and transaction.amount == int(
            result["amount"]
        ):
            success = int(result["status"]) in [1, 2]
            transaction.status = "completed" if success else "failed"
            if success:
                transaction.completed_at = datetime.fromisoformat(result["paidAt"])
                transaction.user.has_paid = True
                transaction.user.save()
                apply_purchase(transaction.items)
                # If the transaction includes 'gamejam', activate the leader's online team
                try:
                    items = json.loads(transaction.items) if transaction.items else []
                    if 'gamejam' in items:
                        OnlineTeam = apps.get_model('gamejam', 'OnlineTeam')
                        team = OnlineTeam.objects.filter(leader=transaction.user, status='inactive').first()
                        if team:
                            team.activate()
                except Exception:
                    logger.exception('Failed to activate online team after purchase')
                # Increment discount code usage count if a discount was applied
                if transaction.discount:
                    DiscountCode.objects.filter(id=transaction.discount.id).update(
                        current_uses=F("current_uses") + 1
                    )
            transaction.card_number = result.get("cardNumber", "")
            transaction.ref_number = int(result.get("refNumber", "0"))
            transaction.gateway_response = result.get("message", "")
            transaction.save()
            transaction.user.save()
            return redirect(
                f"{settings.PAYMENT_SUCCESS_URL if success else settings.PAYMENT_FAILED_URL}"
            )
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
