from django.contrib import admin
from django.utils.html import format_html
from .models import TeamMember, InPersonTeam, OnlineTeam


class InPersonTeamMemberInline(admin.TabularInline):
    model = TeamMember
    fk_name = 'in_person_team'
    extra = 0
    readonly_fields = ['joined_at']
    fields = ['user', 'is_paid', 'payment_completed_at', 'joined_at']
    verbose_name = 'Member'
    verbose_name_plural = 'Members'


class OnlineTeamMemberInline(admin.TabularInline):
    model = TeamMember
    fk_name = 'online_team'
    extra = 0
    readonly_fields = ['joined_at']
    fields = ['user', 'joined_at']
    verbose_name = 'Member'
    verbose_name_plural = 'Members'


class TeamTypeFilter(admin.SimpleListFilter):
    title = 'Team Type'
    parameter_name = 'team_type'
    
    def lookups(self, request, model_admin):
        return (
            ('inperson', 'In-Person Team'),
            ('online', 'Online Team'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'inperson':
            return queryset.filter(in_person_team__isnull=False)
        elif self.value() == 'online':
            return queryset.filter(online_team__isnull=False)


@admin.register(InPersonTeam)
class InPersonTeamAdmin(admin.ModelAdmin):
    model = InPersonTeam
    list_display = (
        'name',
        'leader_email',
        'status',
        'payment_status',
        'member_count',
        'invite_code',
        'created_at',
    )
    list_filter = (
        'status',
        'created_at',
        'leader__is_verified',
        'leader__has_paid',
    )
    search_fields = (
        'name',
        'leader__email',
        'leader__first_name',
        'leader__last_name',
        'invite_code',
        'description',
    )
    readonly_fields = ['invite_code', 'created_at', 'updated_at']
    inlines = [InPersonTeamMemberInline]
    ordering = ['-created_at']
    filter_horizontal = ()

    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description', 'status', 'invite_code')
        }),
        ('Leader Information', {
            'fields': ('leader',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (
            'Team Information',
            {
                'classes': ('wide',),
                'fields': (
                    'name',
                    'description',
                    'leader',
                ),
            },
        ),
    )
    
    def leader_email(self, obj):
        return obj.leader.email
    leader_email.short_description = 'Leader Email'
    leader_email.admin_order_field = 'leader__email'
    
    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = 'Members'
    
    def payment_status(self, obj):
        status = obj.get_payment_status()
        if status['is_paid']:
            return format_html('<span style="color: green;">✓ Fully Paid ({}/{})</span>', 
                             status['paid_members'], status['total_members'])
        else:
            return format_html('<span style="color: orange;">{}/{} Paid</span>', 
                             status['paid_members'], status['total_members'])
    payment_status.short_description = 'Payment Status'


@admin.register(OnlineTeam)
class OnlineTeamAdmin(admin.ModelAdmin):
    model = OnlineTeam
    list_display = (
        'name',
        'leader_email',
        'status',
        'payment_status',
        'member_count',
        'invite_code',
        'created_at',
    )
    list_filter = (
        'status',
        'is_paid',
        'created_at',
        'leader__is_verified',
        'leader__has_paid',
    )
    search_fields = (
        'name',
        'leader__email',
        'leader__first_name',
        'leader__last_name',
        'invite_code',
        'description',
    )
    readonly_fields = ['invite_code', 'created_at', 'updated_at', 'payment_completed_at']
    inlines = [OnlineTeamMemberInline]
    ordering = ['-created_at']
    filter_horizontal = ()

    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description', 'status', 'invite_code')
        }),
        ('Leader Information', {
            'fields': ('leader',)
        }),
        ('Payment Information', {
            'fields': ('is_paid', 'payment_completed_by', 'payment_completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (
            'Team Information',
            {
                'classes': ('wide',),
                'fields': (
                    'name',
                    'description',
                    'leader',
                ),
            },
        ),
    )
    
    def leader_email(self, obj):
        return obj.leader.email
    leader_email.short_description = 'Leader Email'
    leader_email.admin_order_field = 'leader__email'
    
    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = 'Members'
    
    def payment_status(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✓ Paid by {}</span>', 
                             obj.payment_completed_by.email if obj.payment_completed_by else 'Unknown')
        else:
            return format_html('<span style="color: red;">❌ Not Paid</span>')
    payment_status.short_description = 'Payment Status'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    model = TeamMember
    list_display = (
        'user_email',
        'team_info',
        'team_type',
        'is_paid',
        'payment_completed_at',
        'joined_at',
    )
    list_filter = (
        'is_paid',
        TeamTypeFilter,
        'joined_at',
        'in_person_team__status',
        'online_team__status',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'in_person_team__name',
        'online_team__name',
    )
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']
    filter_horizontal = ()

    fieldsets = (
        ('Member Information', {
            'fields': ('user', 'in_person_team', 'online_team')
        }),
        ('Payment Information', {
            'fields': ('is_paid', 'payment_completed_at'),
            'description': 'Payment fields are only relevant for in-person team members'
        }),
        ('System Information', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (
            'Member Information',
            {
                'classes': ('wide',),
                'fields': (
                    'user',
                    'in_person_team',
                    'online_team',
                ),
            },
        ),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def team_info(self, obj):
        if obj.in_person_team:
            return obj.in_person_team.name
        elif obj.online_team:
            return obj.online_team.name
        return "No Team"
    team_info.short_description = 'Team Name'
    
    def team_type(self, obj):
        if obj.in_person_team:
            return "In-Person"
        elif obj.online_team:
            return "Online"
        return "Unknown"
    team_type.short_description = 'Team Type'
    team_type.admin_order_field = 'in_person_team__name'

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:  # editing an existing object
            return readonly_fields + ('joined_at',)
        return readonly_fields