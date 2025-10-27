import json
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
from .models import Announcement, UserAnnouncement


User = get_user_model()


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)
    inlines = []


class UserAnnouncementInline(admin.TabularInline):
    model = UserAnnouncement
    extra = 0
    can_delete = False
    readonly_fields = ("user", "created_at")


AnnouncementAdmin.inlines = [UserAnnouncementInline]


@admin.register(UserAnnouncement)
class UserAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("announcement", "user", "created_at")
    search_fields = ("announcement__title", "user__email")
    list_filter = ("created_at",)
    readonly_fields = ("announcement", "user", "created_at")



class AnnouncementListFilter(admin.SimpleListFilter):
    title = 'announcement'
    parameter_name = 'announcement'

    def lookups(self, request, model_admin):
        # show the most recent 20 announcements
        items = Announcement.objects.order_by('-created_at')[:20]
        return [(str(i.id), i.title[:50]) for i in items]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(announcement_id=val)
        return queryset


UserAnnouncementAdmin.list_filter = ('created_at', AnnouncementListFilter)
