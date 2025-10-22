from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        "email",
        "full_name",
        "phone_number",
        "national_code",
        "university",
        "city",
        "is_verified",
        "has_paid",
        "profile_completed",
        "status",
        "is_staff",
        "created_at",
    )
    list_filter = (
        "is_verified",
        "has_paid",
        "profile_completed",
        "status",
        "is_staff",
        "is_superuser",
        "is_active",
        "gender",
        "university",
        "city",
        "created_at",
        "email_verified_at",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "national_code",
        "university",
        "city",
        "major",
    )
    ordering = ("-created_at",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "national_code",
                    "phone_number",
                    "gender",
                    "birth_date",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "university",
                    "major",
                    "city",
                )
            },
        ),
        (
            "Status & Verification",
            {
                "fields": (
                    "is_verified",
                    "status",
                    "has_paid",
                    "profile_completed",
                    "verification_code",
                    "code_updated_at",
                    "try_count",
                    "email_verified_at",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "last_login",
                    "last_login_ip",
                    "created_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "national_code",
                    "phone_number",
                    "gender",
                    "university",
                    "city",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "last_login",
        "email_verified_at",
        "code_updated_at",
    )

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    full_name.short_description = "Full Name"
    full_name.admin_order_field = "first_name"

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # editing an existing object
            return readonly_fields + (
                "verification_code",
                "code_updated_at",
                "email_verified_at",
            )
        return readonly_fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


admin.site.register(User, CustomUserAdmin)
