from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Payment(models.Model):
    """
    Payment model to track individual and team payments.
    This is a basic implementation that can be extended later.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('individual', 'Individual Payment'),
        ('team', 'Team Payment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # For team payments, this will be set
    team_id = models.PositiveIntegerField(null=True, blank=True, help_text="Team ID for team payments")
    
    # Payment gateway information
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.amount} - {self.status}"


class PaymentMethod(models.Model):
    """
    Payment methods available for users.
    """
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    gateway_config = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name