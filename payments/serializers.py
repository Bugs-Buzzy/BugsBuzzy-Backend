from rest_framework import serializers


class PriceQuerySerializer(serializers.Serializer):
    """Serializer for price query"""
    items = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False
    )


class DiscountQuerySerializer(serializers.Serializer):
    """Serializer for discount query"""
    code = serializers.CharField(required=True)
    items = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False
    )


class PaymentRequestSerializer(serializers.Serializer):
    """Serializer for payment request"""
    items = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False
    )
    discount_code = serializers.CharField(required=False, allow_blank=True)


class CallbackSerializer(serializers.Serializer):
    """Serializer for payment callback"""
    # This is typically for webhook data from payment gateway
    pass


class PurchasedItemsSerializer(serializers.Serializer):
    """Serializer for purchased items response"""
    purchased_items = serializers.ListField(child=serializers.CharField())
    total_transactions = serializers.IntegerField()
    total_spent = serializers.IntegerField()
