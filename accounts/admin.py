import uuid

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User
from django import forms
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.db.models import Q

# announcement models
from announcement.models import Announcement, UserAnnouncement
from payments.models import PurchasingItem, Transaction


class UserInPersonMembership(admin.SimpleListFilter):
    title = "user in-person team membership"
    parameter_name = "in_person_membership"

    def lookups(self, request, model_admin):
        return [
            ("no-team", "no-team"),
            ("member", "member"),
            ("leader", "leader"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "no-team":
            return queryset.filter(
                led_inperson_teams__isnull=True, inperson_memberships__isnull=True
            ).distinct()
        if self.value() == "member":
            return (
                queryset.filter(inperson_memberships__isnull=False)
                .exclude(led_inperson_teams__isnull=False)
                .distinct()
            )
        if self.value() == "leader":
            return queryset.filter(led_inperson_teams__isnull=False).distinct()


class UserOnlineMembership(admin.SimpleListFilter):
    title = "user online team membership"
    parameter_name = "online_membership"

    def lookups(self, request, model_admin):
        return [
            ("no-team", "no-team"),
            ("member", "member"),
            ("leader", "leader"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "no-team":
            return queryset.filter(
                led_gamejam_teams__isnull=True, gamejam_memberships__isnull=True
            ).distinct()
        if self.value() == "member":
            return (
                queryset.filter(gamejam_memberships__isnull=False)
                .exclude(led_gamejam_teams__isnull=False)
                .distinct()
            )
        if self.value() == "leader":
            return queryset.filter(led_gamejam_teams__isnull=False).distinct()


class UserInPersonTeamStatus(admin.SimpleListFilter):
    title = "user in-person team status"
    parameter_name = "in_person_team_status"
    CHOICES = [
        ("incomplete", "Incomplete"),
        ("active", "Active"),
        ("attended", "Attended"),
        ("disbanded", "Disbanded"),
    ]

    def lookups(self, request, model_admin):
        return self.CHOICES

    def queryset(self, request, queryset):
        for choice in self.CHOICES:
            if choice[0] == self.value():
                return queryset.filter(
                    Q(led_inperson_teams__status=choice[0])
                    | Q(inperson_memberships__team__status=choice[0])
                ).distinct()


class UserOnlineTeamStatus(admin.SimpleListFilter):
    title = "user online team status"
    parameter_name = "online_team_status"
    CHOICES = [
        ("inactive", "Inactive"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("attended", "Attended"),
    ]

    def lookups(self, request, model_admin):
        return self.CHOICES

    def queryset(self, request, queryset):
        for choice in self.CHOICES:
            if choice[0] == self.value():
                return queryset.filter(
                    Q(led_gamejam_teams__status=choice[0])
                    | Q(gamejam_memberships__team__status=choice[0])
                ).distinct()


class PurchasingItemListFilter(admin.SimpleListFilter):
    title = "purchasing item"
    parameter_name = "purchasing_item"

    def lookups(self, request, model_admin):
        items = PurchasingItem.objects.order_by("name")
        return [(i.name, i.name) for i in items]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        user_ids = Transaction.objects.filter(items__icontains=val, status="Completed").values_list(
            "user_id", flat=True
        )
        return queryset.filter(id__in=user_ids)


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
        UserInPersonMembership,
        UserOnlineMembership,
        UserInPersonTeamStatus,
        UserOnlineTeamStatus,
        PurchasingItemListFilter,
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
    actions = ["create_announcement_for_selected"]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        is_selection_view = request.GET.get("_popup") and request.GET.get("select_for") == "announcement"
        if is_selection_view:
            extra_context["is_announcement_selection"] = True
            mutable_get = request.GET.copy()
            mutable_get.pop("select_for", None)
            request.GET = mutable_get
        return super().changelist_view(request, extra_context=extra_context)

    def create_announcement_for_selected(self, request, queryset):
        """Redirect to a custom admin view to enter announcement details for the selected users."""

        selected_ids = list(
            queryset.values_list("pk", flat=True)
        )  # includes select-across selections
        if not selected_ids:
            self.message_user(request, "No users selected.", level=messages.WARNING)
            return None

        selection_token = uuid.uuid4().hex
        session_key = f"announcement_selection_{selection_token}"
        request.session[session_key] = [int(pk) for pk in selected_ids]
        request.session.modified = True

        return redirect(f"create_announcement/?token={selection_token}")

    create_announcement_for_selected.short_description = "Create Announcement for selected users"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "create_announcement/",
                self.admin_site.admin_view(self.create_announcement_view),
                name="create-announcement",
            ),
        ]
        return custom + urls

    class AnnouncementCreateForm(forms.Form):
        existing_announcement = forms.ModelChoiceField(
            queryset=Announcement.objects.order_by("-created_at"),
            required=False,
            label="Existing Announcement",
        )
        title = forms.CharField(
            max_length=255,
            required=False,
            label="Announcement Title",
            help_text="If no existing announcement is selected, enter a new title.",
        )
        description = forms.CharField(
            widget=forms.Textarea,
            required=False,
            label="Announcement Description (Markdown allowed)",
            help_text="You can write text with Markdown or simple HTML.",
        )

        def clean(self):
            cleaned_data = super().clean()
            announcement = cleaned_data.get("existing_announcement")
            title = cleaned_data.get("title")
            if not announcement and not title:
                raise forms.ValidationError(
                    "Either select an existing announcement or enter a new title."
                )
            return cleaned_data

    def create_announcement_view(self, request):
        token = request.GET.get("token") or request.POST.get("token")
        ids_param = (
            request.GET.get("ids") if request.method == "GET" else request.POST.get("ids", "")
        )

        session_key = f"announcement_selection_{token}" if token else None
        session_ids = request.session.get(session_key, []) if session_key else []

        if session_ids:
            user_ids = [int(pk) for pk in session_ids]
        else:
            user_ids = [int(x) for x in (ids_param or "").split(",") if x.strip().isdigit()]

        # ensure uniqueness and maintain selection order
        seen = set()
        ordered_user_ids = []
        for pk in user_ids:
            if pk not in seen:
                seen.add(pk)
                ordered_user_ids.append(pk)

        if not ordered_user_ids:
            self.message_user(
                request,
                "No users selected to send announcement.",
                level=messages.WARNING,
            )
            return redirect("..")

        users_map = {
            user.id: user
            for user in User.objects.filter(id__in=ordered_user_ids).only(
                "id", "email", "first_name", "last_name"
            )
        }
        users = [users_map[pk] for pk in ordered_user_ids if pk in users_map]

        if not users:
            self.message_user(
                request,
                "No users found to send announcement.",
                level=messages.WARNING,
            )
            if session_key and session_key in request.session:
                del request.session[session_key]
                request.session.modified = True
            return redirect("..")

        if request.method == "POST":
            form = self.AnnouncementCreateForm(request.POST)
            if form.is_valid():
                announcement = form.cleaned_data.get("existing_announcement")
                created_announcement = False

                if announcement is None:
                    announcement = Announcement.objects.create(
                        title=form.cleaned_data["title"],
                        description=form.cleaned_data.get("description"),
                    )
                    created_announcement = True

                created_links = 0
                skipped_links = 0
                triggered_sends = 0
                for user in users:
                    user_announcement, created = UserAnnouncement.objects.get_or_create(
                        announcement=announcement,
                        user=user,
                    )
                    if created:
                        created_links += 1
                        triggered_sends += 1  # email will be sent via signals
                    elif not user_announcement.email_sent_at:
                        # Attempt to send if the record exists but email was never sent
                        try:
                            if user_announcement.send_email():
                                triggered_sends += 1
                        except Exception as exc:
                            messages.error(
                                request,
                                f"Failed to send email to {user.email}: {exc}",
                            )
                    else:
                        skipped_links += 1

                if created_announcement:
                    self.message_user(
                        request,
                        f"New announcement created and registered for {created_links} users.",
                    )
                else:
                    self.message_user(
                        request,
                        f"Selected announcement registered for {created_links} new users and {skipped_links} were duplicates.",
                    )

                if triggered_sends:
                    self.message_user(
                        request,
                        f"Email will be sent to {triggered_sends} users.",
                    )

                if session_key and session_key in request.session:
                    del request.session[session_key]
                    request.session.modified = True
                return redirect("..")
        else:
            form = self.AnnouncementCreateForm()

        context = dict(self.admin_site.each_context(request))
        context.update(
            {
                "form": form,
                "users_count": len(users),
                "sample_users": users[:10],
                "selection_token": token,
                "raw_ids": ids_param,
            }
        )
        return TemplateResponse(request, "admin/announcement/create_from_users.html", context)


admin.site.register(User, CustomUserAdmin)
