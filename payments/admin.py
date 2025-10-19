from django.contrib import admin
from .models import Payment, PaymentMethod


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'status', 'payment_type', 'team_id', 'created_at']
    list_filter = ['status', 'payment_type', 'created_at']
    search_fields = ['user__email', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']