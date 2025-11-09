from django.db import models


class LobbyGameStatus(models.Model):
    request_uuid = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description


class LobbygameResult(models.Model):
    request_uuid = models.CharField(
        max_length=64, unique=True, null=True, blank=True, verbose_name="Request UUID"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    discount_percentage = models.PositiveIntegerField(null=True, blank=True)
    coupon_code = models.CharField(max_length=32, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lobby Game Result"
        verbose_name_plural = "Lobby Game Results"

    def __str__(self):
        return self.request_uuid or "Lobbygame Result"

    @classmethod
    def get_or_none(cls, request_uuid: str):
        try:
            return cls.objects.get(request_uuid=request_uuid)
        except cls.DoesNotExist:
            return None
