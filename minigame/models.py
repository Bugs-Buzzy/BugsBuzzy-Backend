from django.db import models
from accounts.models import User
from payments.models import DiscountCode


class MinigameResult(models.Model):
    """
    Stores the result of a user's minigame play.
    Each user can only play once.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="minigame_result", verbose_name="User"
    )
    carrot_count = models.PositiveIntegerField(default=0, verbose_name="Carrot Count")
    coin_count = models.PositiveIntegerField(default=0, verbose_name="Coin Count")
    discount_percentage = models.IntegerField(verbose_name="Discount Percentage")
    coupon_code = models.OneToOneField(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minigame_result",
        verbose_name="Coupon Code",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Minigame Result"
        verbose_name_plural = "Minigame Results"

    def __str__(self):
        return f"{self.user.email} - {self.discount_percentage}%"
