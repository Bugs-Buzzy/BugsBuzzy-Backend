from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class DiscountCode(models.Model):
    code = models.CharField(max_length=25, unique=True)
    percentage = models.IntegerField(null=True, blank=True)
    target = models.CharField(max_length=127, null=False, blank=False)
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this code can be used. Leave blank for unlimited uses.",
    )
    current_uses = models.IntegerField(
        default=0, help_text="Number of times this code has been used"
    )

    def is_valid(self):
        """Check if the discount code is still valid (hasn't exceeded max uses)"""
        if self.max_uses is None:
            return True
        return self.current_uses < self.max_uses

    def __str__(self):
        return f"{self.code} - {self.percentage}%"


class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.IntegerField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    items = models.CharField(max_length=255, null=False, blank=False)
    discount = models.ForeignKey(DiscountCode, on_delete=models.PROTECT, null=True, blank=True)

    # Payment gateway information
    track_id = models.CharField(max_length=25, null=False, blank=False, unique=True)
    order_id = models.CharField(max_length=25, null=False, blank=False)
    gateway_response = models.CharField(null=True, blank=True)
    result = models.IntegerField(null=True, blank=True)
    card_number = models.CharField(null=True, blank=True)
    ref_number = models.BigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.amount} - {self.status}"


class PurchasingItem(models.Model):
    COLOR_CHOICES = [
        ("#10b981", "🟢 Green"),
        ("#3b82f6", "🔵 Blue"),
        ("#f59e0b", "🟠 Orange"),
        ("#ef4444", "🔴 Red"),
        ("#8b5cf6", "🟣 Purple"),
        ("#ec4899", "🩷 Pink"),
        ("#14b8a6", "🩵 Teal"),
        ("#6b7280", "⚫ Gray"),
    ]

    name = models.CharField(null=False, blank=False, unique=True)
    description = models.CharField(null=True, blank=True)
    amount = models.IntegerField(null=False, blank=False)  # in Toman
    initial_count = models.IntegerField(null=False, blank=False)
    purchased_count = models.IntegerField(null=False, blank=False)
    color = models.CharField(
        max_length=7,
        default="#6b7280",
        choices=COLOR_CHOICES,
        help_text="Select a color for admin display",
    )

    @property
    def count(self):
        return self.initial_count - self.purchased_count
