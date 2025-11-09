from rest_framework import serializers
from .models import LobbygameResult


class LobbygameResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LobbygameResult
        fields = [
            "request_uuid",
            "description",
            "discount_percentage",
            "coupon_code",
            "created_at",
        ]


class LobbygameSubmissionSerializer(serializers.Serializer):
    def validate(self, data):
        return data
