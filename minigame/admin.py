from django.contrib import admin
from .models import MinigameResult


@admin.register(MinigameResult)
class MinigameResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "carrot_count",
        "coin_count",
        "discount_percentage",
        "coupon_code",
        "created_at",
    )
    list_filter = ("created_at", "discount_percentage")
    search_fields = ("user__email", "coupon_code__code")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
