from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.db.models import F
from django.db.models.functions import Cast
from django.db.models import IntegerField
from .models import (
    OnlineCompetition,
    OnlineTeam,
    OnlineMember,
    OnlineSubmission,
    MIN_MEMBERS,
    MAX_MEMBERS,
)


@admin.register(OnlineCompetition)
class OnlineCompetitionAdmin(admin.ModelAdmin):
    list_display = ("id", "phase_active_display", "title", "updated_at")
    readonly_fields = ("updated_at",)

    fieldsets = (
        (
            "Competition Settings",
            {"fields": ("phase_active", "title", "description", "start", "end")},
        ),
        ("Metadata", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    @admin.display(description="Phase Active", boolean=True)
    def phase_active_display(self, obj):
        return obj.phase_active

    def has_add_permission(self, request):
        return not OnlineCompetition.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class OnlineMemberInline(admin.TabularInline):
    model = OnlineMember
    extra = 0
    readonly_fields = ("user_info", "joined_at")
    fields = ("user_info", "joined_at")
    can_delete = True

    @admin.display(description="User")
    def user_info(self, obj):
        if obj.user:
            return format_html(
                "{} ({})", obj.user.get_full_name() or obj.user.email, obj.user.email
            )
        return "-"


class TeamSizeFilter(admin.SimpleListFilter):
    title = "team size"
    parameter_name = "team_size"

    def lookups(self, request, model_admin):
        return [
            ("complete", f"Complete (>= {MIN_MEMBERS})"),
            ("incomplete", f"Incomplete (< {MIN_MEMBERS})"),
            ("full", f"Full ({MAX_MEMBERS})"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.annotate(member_count_calc=Count("members"))
        if self.value() == "complete":
            # Leader + members >= min
            return queryset.filter(member_count_calc__gte=MIN_MEMBERS - 1)
        if self.value() == "incomplete":
            # Leader + members < min
            return queryset.filter(member_count_calc__lt=MIN_MEMBERS - 1)
        if self.value() == "full":
            # Leader + members = max
            return queryset.filter(member_count_calc=MAX_MEMBERS - 1)
        return queryset


@admin.register(OnlineTeam)
class OnlineTeamAdmin(admin.ModelAdmin):
    list_display = (
        "team_number",
        "name",
        "leader_info",
        "status_display",
        "member_count_display",
        "invite_code",
        "created_at",
    )
    list_filter = ("status", TeamSizeFilter, "created_at")
    search_fields = (
        "team_number",
        "name",
        "leader__email",
        "leader__first_name",
        "leader__last_name",
        "invite_code",
    )
    readonly_fields = (
        "team_number",
        "invite_code",
        "created_at",
        "updated_at",
        "member_count_display",
    )
    inlines = [OnlineMemberInline]
    actions = ["mark_as_active", "mark_as_attended", "mark_as_completed"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Info", {"fields": ("team_number", "name", "description", "leader", "status")}),
        (
            "Team Details",
            {
                "fields": (
                    "invite_code",
                    "member_count_display",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    ordering = ['id']  # Default ordering by id
    
    def get_ordering(self, request):
        """Custom ordering to handle numeric sorting of team_number"""
        ordering = request.GET.get('o', None)
        if ordering == '1' or ordering == '-1':  # team_number column
            # For team_number column, we'll handle numeric sorting in get_queryset
            return ['team_number'] if ordering == '1' else ['-team_number']
        return super().get_ordering(request)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Check if we're ordering by team_number and apply numeric casting
        ordering = self.get_ordering(request)
        if ordering and ('team_number' in ordering[0]):
            direction = '-' if ordering[0].startswith('-') else ''
            qs = qs.annotate(team_number_int=Cast(F('team_number'), IntegerField()))
            qs = qs.order_by(f'{direction}team_number_int')
        return qs

    @admin.display(description="Leader", ordering="leader__email")
    def leader_info(self, obj):
        if obj.leader:
            full_name = obj.leader.get_full_name()
            return format_html(
                '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
                full_name or obj.leader.email,
                obj.leader.email,
            )
        return "-"

    @admin.display(description="Status")
    def status_display(self, obj):
        colors = {
            "inactive": "#6b7280",
            "active": "#3b82f6",
            "completed": "#10b981",
            "attended": "#8b5cf6",
        }
        labels = {
            "inactive": "⏳ Inactive",
            "active": "💰 Active",
            "completed": "✅ Complete",
            "attended": "🎯 Attended",
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.status, "#6b7280"),
            labels.get(obj.status, obj.status),
        )

    @admin.display(description="Members")
    def member_count_display(self, obj):
        count = obj.member_count
        if count >= MIN_MEMBERS:
            color = "#10b981"
        else:
            color = "#f59e0b"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} / {}</span>', color, count, MAX_MEMBERS
        )

    @admin.action(description="Mark selected teams as Active")
    def mark_as_active(self, request, queryset):
        for team in queryset:
            team.activate()
        self.message_user(request, f"{queryset.count()} team(s) marked as active.")

    @admin.action(description="Mark selected teams as Attended")
    def mark_as_attended(self, request, queryset):
        for team in queryset:
            team.mark_attended()
        self.message_user(request, f"{queryset.count()} team(s) marked as attended.")

    @admin.action(description="Mark selected teams as Completed")
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status="completed")
        self.message_user(request, f"{updated} team(s) marked as completed.")


@admin.register(OnlineMember)
class OnlineMemberAdmin(admin.ModelAdmin):
    list_display = ("team_name", "user_info", "joined_at")
    list_filter = ("team__status", "joined_at")
    search_fields = ("team__name", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "joined_at"

    @admin.display(description="Team", ordering="team__name")
    def team_name(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
            obj.team.name,
            obj.team.get_status_display(),
        )

    @admin.display(description="User", ordering="user__email")
    def user_info(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return format_html(
                '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
                full_name or obj.user.email,
                obj.user.email,
            )
        return "-"


@admin.register(OnlineSubmission)
class OnlineSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "team__team_number",
        "team",
        "submitted_by",
        "phase_display",
        "is_final_display",
        "score_display",
        "submitted_at",
    )
    list_filter = ("phase", "submitted_at", "submitted_by", "is_final")
    search_fields = ("team__name", "content")
    readonly_fields = ("submitted_at", "updated_at", "content_preview", "submitted_by")

    fieldsets = (
        (
            "Submission Info",
            {
                "fields": (
                    "team",
                    "submitted_by",
                    "is_final",
                    "phase",
                    "content_preview",
                    "submitted_at",
                    "updated_at",
                )
            },
        ),
        ("Judging", {"fields": ("score", "judge_notes")}),
    )

    @admin.display(description="Phase", ordering="phase")
    def phase_display(self, obj):
        return f"🎮 Phase {obj.phase}"

    @admin.display(description="Score")
    def score_display(self, obj):
        if obj.score is not None:
            color = "#10b981" if obj.score >= 70 else "#f59e0b" if obj.score >= 50 else "#ef4444"
            return format_html(
                '<span style="color:{};font-weight:bold;">{}/100</span>', color, obj.score
            )
        return format_html('<span style="color:#6b7280;">Not scored</span>')

    @admin.display(description="Content")
    def content_preview(self, obj):
        if obj.content:
            preview = obj.content[:200] + "..." if len(obj.content) > 200 else obj.content
            return format_html(
                '<div style="white-space:pre-wrap;max-width:600px;">{}</div>', preview
            )
        return "-"

    @admin.display(description="Final")
    def is_final_display(self, obj):
        return format_html(
            '<span style="font-weight:bold;color:{}">{}</span>',
            "#10b981" if obj.is_final else "#6b7280",
            "YES" if obj.is_final else "no",
        )

    @admin.action(description="Mark selected submission(s) as Final")
    def mark_as_final(self, request, queryset):
        # Only one final per team+phase - so mark others false first per item
        for submission in queryset:
            OnlineSubmission.objects.filter(
                team=submission.team, phase=submission.phase, is_final=True
            ).update(is_final=False)
            submission.is_final = True
            submission.save(update_fields=["is_final"])
        self.message_user(request, f"Marked {queryset.count()} submission(s) as final.")

    actions = [mark_as_final]
