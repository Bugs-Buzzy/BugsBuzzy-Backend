from rest_framework import serializers

from .models import Workshop


class WorkshopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workshop
        fields = (
            "id",
            "title",
            "description",
            "start_datetime",
            "duration",
            "presenter",
            "presenter_image",
            "vc_link",
            "place",
            "record_link",
        )
