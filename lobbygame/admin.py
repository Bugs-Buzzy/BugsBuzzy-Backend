from django.contrib import admin
from .models import LobbygameResult


@admin.register(LobbygameResult)
class LobbygameResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_uuid",
        "description",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("request_uuid", "description")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return True  # Allow creating entries manually in admin

    def has_change_permission(self, request, obj=None):
        return True  # Allow editing
