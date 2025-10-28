from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User
from django import forms
from django.shortcuts import render, redirect
from django.urls import path

# announcement models
from announcement.models import Announcement, UserAnnouncement


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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make optional fields not required in admin
        if "university" in form.base_fields:
            form.base_fields["university"].required = False
        if "major" in form.base_fields:
            form.base_fields["major"].required = False
        if "birth_date" in form.base_fields:
            form.base_fields["birth_date"].required = False
        return form

    # Admin action: create announcement for selected users
    actions = ['create_announcement_for_selected']

    def create_announcement_for_selected(self, request, queryset):
        """Redirect to a custom admin view to enter announcement details for the selected users."""
        selected = request.POST.getlist('_selected_action')
        if not selected:
            self.message_user(request, "No users selected.", level=messages.WARNING)
            return
        ids = ",".join(selected)
        return redirect(f"create_announcement/?ids={ids}")

    create_announcement_for_selected.short_description = "Create Announcement for selected users"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('create_announcement/', self.admin_site.admin_view(self.create_announcement_view), name='create-announcement'),
        ]
        return custom + urls

    class AnnouncementCreateForm(forms.Form):
        title = forms.CharField(max_length=255)
        description = forms.CharField(widget=forms.Textarea, required=False)
    # always send email; no subject override

    def create_announcement_view(self, request):
        ids = request.GET.get('ids', '')
        user_ids = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        users = User.objects.filter(id__in=user_ids)

        if request.method == 'POST':
            form = self.AnnouncementCreateForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data['title']
                description = form.cleaned_data.get('description')
                # always send and use default subject
                subject = f"Announcement: {title}"

                ann = Announcement.objects.create(title=title, description=description)
                created = 0
                for u in users:
                    UserAnnouncement.objects.get_or_create(announcement=ann, user=u)
                    created += 1

                # synchronous email send (minimal)
                from django.template.loader import render_to_string
                from django.core.mail import send_mail
                from django.conf import settings
                html_body = render_to_string('emails/announcement_email.html', {'announcement': ann})
                for u in users:
                    try:
                        if u.email:
                            send_mail(subject=subject, message=description or '', html_message=html_body, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[u.email], fail_silently=False)
                    except Exception:
                        continue

                self.message_user(request, f"Created announcement and linked to {created} users.")
                return redirect('..')
        else:
            form = self.AnnouncementCreateForm()

        context = dict(self.admin_site.each_context(request))
        context.update({
            'form': form,
            'users_count': users.count(),
        })
        return render(request, 'admin/announcement/create_from_users.html', context)


admin.site.register(User, CustomUserAdmin)
