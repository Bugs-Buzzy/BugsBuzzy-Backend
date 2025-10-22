from django.contrib import admin
from .models import Transaction, DiscountCode, PurchasingItem


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "status",
        "track_id",
        "order_id",
        "ref_number",
        "created_at",
        "completed_at",
    )
    list_filter = ("status",)
    search_fields = (
        "user__email",
        "track_id",
        "order_id",
        "ref_number",
        "card_number",
    )
    readonly_fields = ("created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)


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
        "count",
    )
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Remaining")
    def count(self, obj):
        return obj.count
