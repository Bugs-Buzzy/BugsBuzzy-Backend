from django.contrib import admin
from django.utils.html import format_html
from .models import InPersonCompetition, InPersonTeam, InPersonMember


@admin.register(InPersonCompetition)
class InPersonCompetitionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Phase 0: Introduction', {
            'fields': ('phase_0_active', 'phase_0_title', 'phase_0_description', 'phase_0_start', 'phase_0_end')
        }),
        ('Phase 1: Ideation', {
            'fields': ('phase_1_active', 'phase_1_title', 'phase_1_description', 'phase_1_start', 'phase_1_end')
        }),
        ('Phase 2: Development', {
            'fields': ('phase_2_active', 'phase_2_title', 'phase_2_description', 'phase_2_start', 'phase_2_end')
        }),
        ('Phase 3: Polish', {
            'fields': ('phase_3_active', 'phase_3_title', 'phase_3_description', 'phase_3_start', 'phase_3_end')
        }),
        ('Phase 4: Final Battle', {
            'fields': ('phase_4_active', 'phase_4_title', 'phase_4_description', 'phase_4_start', 'phase_4_end')
        }),
    )
    
    def has_add_permission(self, request):
        return not InPersonCompetition.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


class InPersonMemberInline(admin.TabularInline):
    model = InPersonMember
    extra = 0
    readonly_fields = ('user', 'has_paid', 'joined_at')
    can_delete = True


@admin.register(InPersonTeam)
class InPersonTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'member_count_display', 'paid_count_display', 'invite_code', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'leader__email', 'invite_code')
    readonly_fields = ('invite_code', 'created_at', 'updated_at')
    inlines = [InPersonMemberInline]
    
    @admin.display(description='Members')
    def member_count_display(self, obj):
        return obj.member_count
    
    @admin.display(description='Paid')
    def paid_count_display(self, obj):
        paid = obj.members.filter(has_paid=True).count()
        total = obj.member_count
        color = '#10b981' if paid == total else '#f59e0b'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} / {}</span>',
            color, paid, total
        )


@admin.register(InPersonMember)
class InPersonMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'has_paid', 'joined_at')
    list_filter = ('has_paid', 'joined_at')
    search_fields = ('user__email', 'team__name')
    readonly_fields = ('joined_at',)


# @admin.register(InPersonSubmission)
# class InPersonSubmissionAdmin(admin.ModelAdmin):
#     list_display = ('team', 'phase', 'title', 'score', 'submitted_at')
#     list_filter = ('phase', 'submitted_at')
#     search_fields = ('team__name', 'title')
#     readonly_fields = ('submitted_at', 'updated_at')
