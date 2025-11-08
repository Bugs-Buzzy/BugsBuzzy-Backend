from rest_framework import serializers
from .models import LobbygameResult


class LobbygameResultSerializer(serializers.ModelSerializer):
    coupon_code = serializers.SerializerMethodField()

    class Meta:
        model = LobbygameResult
        fields = ["description"]


class LobbygameSubmissionSerializer(serializers.Serializer):
    def validate(self, data):
        return data
