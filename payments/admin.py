from django.contrib import admin
from django.db.models import Q, Count, Sum
from django.utils.html import format_html
import json
from .models import Transaction, DiscountCode, PurchasingItem
from .models_proxy import UserPurchasesSummary


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "status",
        "purchased_items_display",
        "track_id",
        "order_id",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "user__email",
        "track_id",
        "order_id",
        "ref_number",
        "card_number",
        "items",
    )
    readonly_fields = ("created_at", "updated_at", "completed_at", "purchased_items_display")
    ordering = ("-created_at",)
    
    @admin.display(description="Purchased Items")
    def purchased_items_display(self, obj):
        if obj.status == "completed" and obj.items:
            try:
                items_list = json.loads(obj.items)
                badges = []
                colors = {
                    'inperson': '#10b981',
                    'gamejam': '#3b82f6', 
                    'thursday_lunch': '#f59e0b',
                    'friday_lunch': '#f59e0b',
                }
                for item in items_list:
                    item = item.strip()
                    color = colors.get(item, '#6b7280')
                    badges.append(f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:4px;margin:2px;display:inline-block;font-size:11px;">{item}</span>')
                return format_html(' '.join(badges))
            except (json.JSONDecodeError, TypeError):
                return obj.items
        return '-'


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "percentage", "target", "current_uses", "max_uses", "is_valid_display")
    search_fields = ("code", "target")
    ordering = ("code",)
    readonly_fields = ("current_uses",)

    @admin.display(description="Valid", boolean=True)
    def is_valid_display(self, obj):
        return obj.is_valid()


@admin.register(PurchasingItem)
class PurchasingItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "amount",
        "initial_count",
        "purchased_count",
        "remaining_display",
        "buyers_count",
    )
    search_fields = ("name",)
    ordering = ("name",)
    
    change_list_template = 'admin/payments/purchasingitem_changelist.html'

    @admin.display(description="Remaining")
    def remaining_display(self, obj):
        remaining = obj.count
        percentage = (remaining / obj.initial_count * 100) if obj.initial_count > 0 else 0
        color = '#10b981' if percentage > 50 else '#f59e0b' if percentage > 20 else '#ef4444'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} / {}</span>',
            color, remaining, obj.initial_count
        )
    
    @admin.display(description="Buyers")
    def buyers_count(self, obj):
        # Get all completed transactions and filter by checking if item is in JSON array
        completed_transactions = Transaction.objects.filter(status='completed')
        count = 0
        for trans in completed_transactions:
            if trans.items:
                try:
                    items = json.loads(trans.items)
                    if obj.name in items:
                        count += 1
                except (json.JSONDecodeError, TypeError):
                    pass
        return count
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get buyers for each item
        items_with_buyers = []
        for item in PurchasingItem.objects.all():
            all_transactions = Transaction.objects.filter(
                status='completed'
            ).select_related('user').order_by('-completed_at')
            
            # Filter transactions that contain this item
            buyers = []
            for trans in all_transactions:
                if trans.items:
                    try:
                        items = json.loads(trans.items)
                        if item.name in items:
                            buyers.append(trans)
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            items_with_buyers.append({
                'item': item,
                'buyers': buyers,
            })
        
        extra_context['items_with_buyers'] = items_with_buyers
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(UserPurchasesSummary)
class UserPurchasesSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'full_name',
        'purchased_items_display',
        'total_spent',
        'transactions_count',
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-id',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only show users who have completed transactions
        return qs.filter(payments__status='completed').distinct()
    
    @admin.display(description='Full Name')
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else '-'
    
    @admin.display(description='Purchased Items')
    def purchased_items_display(self, obj):
        completed_transactions = Transaction.objects.filter(
            user=obj,
            status='completed'
        )
        
        all_items = set()
        for trans in completed_transactions:
            if trans.items:
                try:
                    items = json.loads(trans.items)
                    all_items.update(items)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        if all_items:
            colors = {
                'inperson': '#10b981',
                'gamejam': '#3b82f6',
                'thursday_lunch': '#f59e0b',
                'friday_lunch': '#f59e0b',
            }
            badges = []
            for item in sorted(all_items):
                color = colors.get(item, '#6b7280')
                badges.append(
                    f'<span style="background-color:{color};color:white;'
                    f'padding:3px 10px;border-radius:4px;margin:2px;'
                    f'display:inline-block;font-size:12px;">{item}</span>'
                )
            return format_html(' '.join(badges))
        return '-'
    
    @admin.display(description='Total Spent')
    def total_spent(self, obj):
        total = Transaction.objects.filter(
            user=obj,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return format_html(
            '<span style="color:#10b981;font-weight:bold;">{:,} تومان</span>',
            total
        )
    
    @admin.display(description='Transactions')
    def transactions_count(self, obj):
        count = Transaction.objects.filter(
            user=obj,
            status='completed'
        ).count()
        return count
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
