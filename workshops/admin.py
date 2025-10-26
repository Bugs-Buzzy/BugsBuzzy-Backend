from django.contrib import admin

from .models import Workshop


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ("title", "start_datetime", "duration", "presenter")
    search_fields = ("title", "presenter")
