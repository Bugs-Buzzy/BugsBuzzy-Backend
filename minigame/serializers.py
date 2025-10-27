from rest_framework import serializers
from .models import MinigameResult


class MinigameResultSerializer(serializers.ModelSerializer):
    coupon_code = serializers.SerializerMethodField()

    class Meta:
        model = MinigameResult
        fields = ["carrot_count", "coin_count", "discount_percentage", "coupon_code", "created_at"]
        read_only_fields = ["discount_percentage", "coupon_code", "created_at"]

    def get_coupon_code(self, obj):
        if obj.coupon_code:
            return {"code": obj.coupon_code.code, "percentage": obj.coupon_code.percentage}
        return None


class MinigameSubmissionSerializer(serializers.Serializer):
    carrot_count = serializers.IntegerField(min_value=0, max_value=300)
    coin_count = serializers.IntegerField(min_value=0, max_value=20)

    def validate(self, data):
        carrot_count = data.get("carrot_count", 0)
        coin_count = data.get("coin_count", 0)

        if carrot_count > 300 or coin_count > 20:
            raise serializers.ValidationError("Invalid scores detected. Please play fairly.")

        return data
