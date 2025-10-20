import requests
import random
from datetime import datetime
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsVerified, ProfileCompleted
from django.conf import settings
from .models import Transaction, DiscountCode
from .utils import calculate_amount


class PriceView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def get(self, request):
        discount_code = request.GET.get("discount_code", "")
        items = request.GET.get("items", [])
        
        if len(items) == 0:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()
        amount = calculate_amount(items, discount)
        
        return Response(
            {"amount": int(amount), "discount_applied": True if discount else False},
            status=status.HTTP_200_OK,
        )


class PaymentView(APIView):
    permission_classes = [IsAuthenticated, IsVerified, ProfileCompleted]

    def post(self, request):
        user = request.user            
        discount_code = request.GET.get("discount_code", "")
        items = request.GET.get("items", [])
        
        if len(items) == 0:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        discount = DiscountCode.objects.filter(code__iexact=discount_code.lower()).first()
        amount = calculate_amount(items, discount)
        order_id = random.randint(100000, 999999)

        response = requests.post(
            "https://gateway.zibal.ir/request/lazy",
            json={
                "merchant": settings.MERCHANT_ID,
                "amount": int(amount),
                "callbackUrl": "https://bugsbuzzy.ir/api/payment/callback",
                "description": "BugsBuzzy Payment\n" + str(items),
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
                items=str(items),
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
    def post(self, request):
        data = request.data
        
        # if int(data["success"]) == 1:
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
        if transaction.order_id == str(result["orderId"]) and transaction.amount == int(result["amount"]):
            success = int(result["status"]) in [1, 2]
            transaction.status = "completed" if success else "failed"
            if success:
                transaction.completed_at = datetime.fromisoformat(result["paidAt"])
            transaction.card_number = result["cardNumber"]
            transaction.ref_number = int(result["refNumber"])
            transaction.gateway_response = result["message"]
            transaction.save()
            return redirect(f"https://bugsbuzzy.ir/payment/{'success' if success else 'failed'}")
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
