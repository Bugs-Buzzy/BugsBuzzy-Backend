from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.IntegerField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    items = models.CharField(max_length=255, null=False, blank=False)
    
    # Payment gateway information
    track_id = models.CharField(max_length=25, null=False, blank=False, unique=True)
    order_id = models.CharField(max_length=25, null=False, blank=False)
    gateway_response = models.CharField(null=True, blank=True)
    result = models.IntegerField(null=True, blank=True)
    card_number = models.CharField(null=True, blank=True)
    ref_number = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.amount} - {self.status}"
    
    
class DiscountCode(models.Model):
    code = models.CharField(max_length=25, unique=True)
    percentage = models.IntegerField(null=True, blank=True)
    target = models.CharField(max_length=127, null=False, blank=False)


class PurchasingItem(models.Model):
    name = models.CharField(null=False, blank=False, unique=True)
    description = models.CharField(null=True, blank=True)
    amount = models.IntegerField(null=False, blank=False)   # in Toman
    initial_count = models.IntegerField(null=False, blank=False)
    purchased_count = models.IntegerField(null=False, blank=False)
    
    @property
    def count(self):
        return self.initial_count - self.purchased_count
    