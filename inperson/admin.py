from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import InPersonCompetition, InPersonTeam, InPersonMember


@admin.register(InPersonCompetition)
class InPersonCompetitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'active_phases_display', 'updated_at')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        ('Phase 0: Introduction', {
            'fields': ('phase_0_active', 'phase_0_title', 'phase_0_description', 'phase_0_start', 'phase_0_end'),
            'classes': ('collapse',)
        }),
        ('Phase 1: Ideation', {
            'fields': ('phase_1_active', 'phase_1_title', 'phase_1_description', 'phase_1_start', 'phase_1_end'),
            'classes': ('collapse',)
        }),
        ('Phase 2: Development', {
            'fields': ('phase_2_active', 'phase_2_title', 'phase_2_description', 'phase_2_start', 'phase_2_end'),
            'classes': ('collapse',)
        }),
        ('Phase 3: Polish', {
            'fields': ('phase_3_active', 'phase_3_title', 'phase_3_description', 'phase_3_start', 'phase_3_end'),
            'classes': ('collapse',)
        }),
        ('Phase 4: Final Battle', {
            'fields': ('phase_4_active', 'phase_4_title', 'phase_4_description', 'phase_4_start', 'phase_4_end'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Active Phases')
    def active_phases_display(self, obj):
        active = []
        for i in range(5):
            if getattr(obj, f'phase_{i}_active'):
                active.append(f'P{i}')
        if not active:
            return format_html('<span style="color:#6b7280;">None</span>')
        return format_html(
            '<span style="color:#10b981; font-weight:bold;">{}</span>',
            ', '.join(active)
        )
    
    def has_add_permission(self, request):
        return not InPersonCompetition.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


class InPersonMemberInline(admin.TabularInline):
    model = InPersonMember
    extra = 0
    readonly_fields = ('user_info', 'payment_status_display', 'joined_at')
    fields = ('user_info', 'payment_status_display', 'joined_at')
    can_delete = True
    
    @admin.display(description='User')
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '{} ({})',
                obj.user.get_full_name() or obj.user.email,
                obj.user.email
            )
        return '-'
    
    @admin.display(description='Payment')
    def payment_status_display(self, obj):
        if obj.user.has_paid:
            return format_html('<span style="color:#10b981; font-weight:bold;">✅ Paid</span>')
        return format_html('<span style="color:#f59e0b; font-weight:bold;">⏳ Pending</span>')


class TeamSizeFilter(admin.SimpleListFilter):
    title = 'team size'
    parameter_name = 'size'
    
    def lookups(self, request, model_admin):
        return (
            ('ready', 'Ready (≥3 members)'),
            ('incomplete', 'Incomplete (<3 members)'),
            ('full', 'Full (5 members)'),
        )
    
    def queryset(self, request, queryset):
        queryset = queryset.annotate(member_count_calc=Count('members'))
        if self.value() == 'ready':
            # Leader + members >= 3
            return queryset.filter(member_count_calc__gte=2)
        if self.value() == 'incomplete':
            # Leader + members < 3
            return queryset.filter(member_count_calc__lt=2)
        if self.value() == 'full':
            # Leader + members = 5
            return queryset.filter(member_count_calc=4)
        return queryset


@admin.register(InPersonTeam)
class InPersonTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader_info', 'status_display', 'member_count_display', 'paid_count_display', 'invite_code', 'created_at')
    list_filter = ('status', TeamSizeFilter, 'created_at')
    search_fields = ('name', 'leader__email', 'leader__first_name', 'leader__last_name', 'invite_code')
    readonly_fields = ('invite_code', 'created_at', 'updated_at', 'member_count_display')
    inlines = [InPersonMemberInline]
    actions = ['mark_as_active', 'mark_as_attended', 'mark_as_incomplete']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'leader', 'status')
        }),
        ('Team Details', {
            'fields': ('invite_code', 'member_count_display', 'created_at', 'updated_at')
        }),
    )
    
    @admin.display(description='Leader', ordering='leader__email')
    def leader_info(self, obj):
        if obj.leader:
            full_name = obj.leader.get_full_name()
            return format_html(
                '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
                full_name or obj.leader.email,
                obj.leader.email
            )
        return '-'
    
    @admin.display(description='Status')
    def status_display(self, obj):
        colors = {
            'incomplete': '#f59e0b',
            'active': '#10b981',
            'attended': '#3b82f6',
            'disbanded': '#ef4444',
        }
        labels = {
            'incomplete': '⚠️ Incomplete',
            'active': '✅ Active',
            'attended': '🎯 Attended',
            'disbanded': '❌ Disbanded',
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            labels.get(obj.status, obj.status)
        )
    
    @admin.display(description='Members')
    def member_count_display(self, obj):
        count = obj.member_count
        color = '#10b981' if count >= 3 else '#f59e0b'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} / 5</span>',
            color, count
        )
    
    @admin.display(description='Paid')
    def paid_count_display(self, obj):
        # Count members who have paid (using user.has_paid)
        members_paid = sum(1 for m in obj.members.all() if m.user.has_paid)
        leader_paid = 1 if obj.leader.has_paid else 0
        
        total_paid = members_paid + leader_paid
        total = obj.member_count
        
        if total_paid == total:
            color = '#10b981'
            icon = '✅'
        elif total_paid > 0:
            color = '#f59e0b'
            icon = '⏳'
        else:
            color = '#ef4444'
            icon = '❌'
        
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} {} / {}</span>',
            color, icon, total_paid, total
        )
    
    @admin.action(description='Mark selected teams as Active')
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} team(s) marked as active.')
    
    @admin.action(description='Mark selected teams as Attended')
    def mark_as_attended(self, request, queryset):
        updated = queryset.update(status='attended')
        self.message_user(request, f'{updated} team(s) marked as attended.')
    
    @admin.action(description='Mark selected teams as Incomplete')
    def mark_as_incomplete(self, request, queryset):
        updated = queryset.update(status='incomplete')
        self.message_user(request, f'{updated} team(s) marked as incomplete.')


@admin.register(InPersonMember)
class InPersonMemberAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'team_info', 'payment_status', 'joined_at')
    list_filter = ('joined_at', 'team__status')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'team__name')
    readonly_fields = ('joined_at',)
    
    @admin.display(description='User', ordering='user__email')
    def user_info(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return format_html(
                '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
                full_name or obj.user.email,
                obj.user.email
            )
        return '-'
    
    @admin.display(description='Team', ordering='team__name')
    def team_info(self, obj):
        if obj.team:
            return format_html(
                '<strong>{}</strong><br/><small style="color:#6b7280;">{}</small>',
                obj.team.name,
                obj.team.invite_code
            )
        return '-'
    
    @admin.display(description='Payment', ordering='user__has_paid')
    def payment_status(self, obj):
        if obj.user.has_paid:
            return format_html(
                '<span style="color:#10b981; font-weight:bold;">✅ Paid</span>'
            )
        return format_html(
            '<span style="color:#f59e0b; font-weight:bold;">⏳ Pending</span>'
        )


# @admin.register(InPersonSubmission)
# class InPersonSubmissionAdmin(admin.ModelAdmin):
#     list_display = ('team', 'phase', 'title', 'score', 'submitted_at')
#     list_filter = ('phase', 'submitted_at')
#     search_fields = ('team__name', 'title')
#     readonly_fields = ('submitted_at', 'updated_at')
