from django.contrib import admin, messages

from .emails import send_user_announcement_email
from .models import Announcement, UserAnnouncement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "user_count", "last_sent")
    search_fields = ("title",)
    inlines = []
    actions = ["resend_emails"]

    @admin.display(description="User Count")
    def user_count(self, obj: Announcement) -> int:
        return obj.user_announcements.count()

    @admin.display(description="Last Sent")
    def last_sent(self, obj: Announcement):
        latest = obj.user_announcements.order_by("-email_sent_at").first()
        return latest.email_sent_at if latest else None

    def resend_emails(self, request, queryset):
        sent = 0
        skipped = 0
        failed = 0

        for announcement in queryset:
            for user_announcement in announcement.user_announcements.select_related("user"):
                try:
                    if send_user_announcement_email(user_announcement, force=True):
                        sent += 1
                    else:
                        skipped += 1
                except Exception as exc:  # pragma: no cover - email backend dependent
                    failed += 1
                    messages.error(
                        request,
                        f"Failed to send email to {user_announcement.user.email} due to {exc}.",
                    )

        if sent:
            messages.success(request, f"{sent} emails were resent.")
        if skipped:
            messages.info(request, f"{skipped} emails were already sent and skipped.")
        if failed and not sent:
            messages.error(request, f"Failed to resend {failed} emails.")

    resend_emails.short_description = "Resend emails for selected announcements"


class UserAnnouncementInline(admin.TabularInline):
    model = UserAnnouncement
    extra = 1
    can_delete = True
    autocomplete_fields = ("user",)
    fields = (
        "user",
        "email_sent_at",
        "email_delivered_at",
        "email_send_attempts",
        "email_last_error",
    )
    readonly_fields = (
        "email_sent_at",
        "email_delivered_at",
        "email_send_attempts",
        "email_last_error",
        "created_at",
    )
    show_change_link = True


AnnouncementAdmin.inlines = [UserAnnouncementInline]


@admin.register(UserAnnouncement)
class UserAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "announcement",
        "user",
        "created_at",
        "email_sent_at",
        "email_delivered_at",
        "email_send_attempts",
    )
    search_fields = ("announcement__title", "user__email")
    autocomplete_fields = ("announcement", "user")
    readonly_base_fields = (
        "created_at",
        "email_sent_at",
        "email_delivered_at",
        "email_send_attempts",
        "email_last_error",
    )
    readonly_fields = readonly_base_fields
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "announcement",
                    "user",
                    "created_at",
                    "email_sent_at",
                    "email_delivered_at",
                    "email_send_attempts",
                    "email_last_error",
                )
            },
        ),
    )
    actions = ["send_selected", "force_resend_selected"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (*self.readonly_base_fields, "announcement", "user")
        return self.readonly_base_fields

    def send_selected(self, request, queryset):
        sent = 0
        skipped = 0
        failed = 0
        for user_announcement in queryset.select_related("user", "announcement"):
            try:
                if send_user_announcement_email(user_announcement):
                    sent += 1
                else:
                    skipped += 1
            except Exception as exc:  # pragma: no cover - email backend dependent
                failed += 1
                messages.error(
                    request,
                    f"Failed to send email to {user_announcement.user.email} due to {exc}.",
                )

        if sent:
            messages.success(request, f"Email sent to {sent} users.")
        if skipped:
            messages.info(request, f"{skipped} items were already sent.")
        if failed and not sent:
            messages.error(request, f"Failed to send {failed} emails.")

    send_selected.short_description = "Send email for selected items"

    def force_resend_selected(self, request, queryset):
        resent = 0
        failed = 0
        for user_announcement in queryset.select_related("user", "announcement"):
            try:
                if send_user_announcement_email(user_announcement, force=True):
                    resent += 1
            except Exception as exc:  # pragma: no cover - email backend dependent
                failed += 1
                messages.error(
                    request,
                    f"Failed to resend email to {user_announcement.user.email} due to {exc}.",
                )

        if resent:
            messages.success(request, f"Email resent to {resent} users.")
        if failed and not resent:
            messages.error(request, f"Failed to resend {failed} emails.")

    force_resend_selected.short_description = "Force resend email for selected items"


class AnnouncementListFilter(admin.SimpleListFilter):
    title = "announcement"
    parameter_name = "announcement"

    def lookups(self, request, model_admin):
        # show the most recent 20 announcements
        items = Announcement.objects.order_by("-created_at")[:20]
        return [(str(i.id), i.title[:50]) for i in items]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(announcement_id=val)
        return queryset


UserAnnouncementAdmin.list_filter = ("created_at", "email_sent_at", AnnouncementListFilter)
