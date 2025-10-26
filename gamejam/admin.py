from django.contrib import admin
from .models import OnlineTeam, OnlineMember


@admin.register(OnlineTeam)
class OnlineTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "status", "invite_code")
    search_fields = ("name", "leader__email")


@admin.register(OnlineMember)
class OnlineMemberAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "joined_at")
    search_fields = ("team__name", "user__email")
