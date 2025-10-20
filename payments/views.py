import requests
import random
import json
from datetime import datetime
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsVerified, ProfileCompleted
from django.conf import settings
from .models import Transaction, DiscountCode
from .utils import calculate_amount, apply_purchase


class PriceView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def get(self, request):
        discount_code = request.data.get("discount_code", "")
        items = request.data.get("items", [])
        
        if len(items) == 0:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()
        amount, applied = calculate_amount(items, discount)
        
        return Response(
            {"amount": int(amount), "discount_applied": applied},
            status=status.HTTP_200_OK,
        )


class PaymentView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def post(self, request):
        user = request.user            
        discount_code = request.data.get("discount_code", "")
        items = request.data.get("items", [])
        
        if len(items) == 0:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()
        amount, _ = calculate_amount(items, discount)
        order_id = random.randint(100000, 999999)

        response = requests.post(
            "https://gateway.zibal.ir/request/lazy",
            json={
                "merchant": settings.MERCHANT_ID,
                "amount": int(amount),
                "callbackUrl": "https://bugsbuzzy.ir/api/payment/callback/",
                "description": "BugsBuzzy Payment\n" + json.dumps(items),
                "orderId": str(order_id),
                "mobile": user.phone_number,
                "checkMobileWithCard": False
            },
            timeout=10,
        )

        data = response.json()
        if "result" in data and data["result"] == 100:
            transaction = Transaction.objects.create(
                track_id=str(data["trackId"]),
                order_id=str(order_id),
                user=user,
                items=json.dumps(items),
                amount=int(amount),
                discount=discount,
                gateway_response=data["message"],
                result=int(data["result"])
            )
            return Response({"redirect_url": f"https://gateway.zibal.ir/start/{data['trackId']}"}, status=200)
        else:
            return Response(
                {"error": "Payment service failed"},
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
            json={
                "merchant": settings.MERCHANT_ID,
                "trackId": int(data["trackId"])
            },
            timeout=10,
        )
        
        result = response.json()
        if "status" not in result.keys():
            transaction.status = "failed"
            transaction.gateway_response = result.get("message", "")
            transaction.save()
            return redirect(f"https://bugsbuzzy.ir/payment/failed")
        
        if transaction.order_id == str(result["orderId"]) and transaction.amount == int(result["amount"]):
            success = int(result["status"]) in [1, 2]
            transaction.status = "completed" if success else "failed"
            if success:
                transaction.completed_at = datetime.fromisoformat(result["paidAt"])
                transaction.user.has_paid = True
                transaction.user.save()
                apply_purchase(transaction.items)
            transaction.card_number = result.get("cardNumber", "")
            transaction.ref_number = int(result.get("refNumber", "0"))
            transaction.gateway_response = result.get("message", "")
            transaction.save()
            transaction.user.save()
            return redirect(f"https://bugsbuzzy.ir/payment/{'success' if success else 'failed'}")
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
