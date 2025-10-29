from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import random
import string

User = get_user_model()

MIN_MEMBERS_PER_TEAM = 3
MAX_MEMBERS_PER_TEAM = 3


class InPersonCompetition(models.Model):
    """
    Singleton model to control competition phases and settings.
    Only one instance should exist.
    """

    # Phase 0: Introduction
    phase_0_active = models.BooleanField(default=False, verbose_name="Phase 0 Active")
    phase_0_title = models.CharField(max_length=200, default="فاز ۰: آشنایی")
    phase_0_description = models.TextField(blank=True)
    phase_0_start = models.DateTimeField(null=True, blank=True)
    phase_0_end = models.DateTimeField(null=True, blank=True)

    # Phase 1: Ideation
    phase_1_active = models.BooleanField(default=False, verbose_name="Phase 1 Active")
    phase_1_title = models.CharField(max_length=200, default="فاز ۱: ایده‌پردازی")
    phase_1_description = models.TextField(blank=True)
    phase_1_start = models.DateTimeField(null=True, blank=True)
    phase_1_end = models.DateTimeField(null=True, blank=True)

    # Phase 2: Development
    phase_2_active = models.BooleanField(default=False, verbose_name="Phase 2 Active")
    phase_2_title = models.CharField(max_length=200, default="فاز ۲: پیاده‌سازی")
    phase_2_description = models.TextField(blank=True)
    phase_2_start = models.DateTimeField(null=True, blank=True)
    phase_2_end = models.DateTimeField(null=True, blank=True)

    # Phase 3: Polish
    phase_3_active = models.BooleanField(default=False, verbose_name="Phase 3 Active")
    phase_3_title = models.CharField(max_length=200, default="فاز ۳: زیباسازی")
    phase_3_description = models.TextField(blank=True)
    phase_3_start = models.DateTimeField(null=True, blank=True)
    phase_3_end = models.DateTimeField(null=True, blank=True)

    # Phase 4: Final Battle
    phase_4_active = models.BooleanField(default=False, verbose_name="Phase 4 Active")
    phase_4_title = models.CharField(max_length=200, default="فاز ۴: نبرد پایانی")
    phase_4_description = models.TextField(blank=True)
    phase_4_start = models.DateTimeField(null=True, blank=True)
    phase_4_end = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "In-Person Competition Settings"
        verbose_name_plural = "In-Person Competition Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "In-Person Competition Settings"


class InPersonTeam(models.Model):
    """Team model for in-person competition"""

    STATUS_CHOICES = [
        ("incomplete", "Incomplete"),
        ("active", "Active"),
        ("attended", "Attended"),
        ("disbanded", "Disbanded"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    avatar = models.TextField(blank=True, help_text="Base64 data URI for team avatar (max 256x256)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="incomplete")
    invite_code = models.CharField(max_length=8, unique=True, editable=False)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="led_inperson_teams")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "In-Person Team"
        verbose_name_plural = "In-Person Teams"

    def __str__(self):
        return f"{self.name} (Leader: {self.leader.email})"

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    def generate_invite_code(self):
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not InPersonTeam.objects.filter(invite_code=code).exists():
                return code

    def revoke_invite_code(self):
        """Revoke current invite code and generate new one"""
        self.invite_code = self.generate_invite_code()
        self.save(update_fields=["invite_code"])

    def disband(self):
        """Disband the team"""
        self.status = "disbanded"
        self.invite_code = None
        self.save(update_fields=["status", "invite_code"])

    def mark_attended(self):
        """Mark team as attended"""
        self.status = "attended"
        self.save(update_fields=["status"])

    def activate(self):
        """Activate team when minimum requirements met"""
        self.status = "active"
        self.save(update_fields=["status"])

    @property
    def member_count(self):
        return self.members.count() + 1  # +1 for leader

    def is_member(self, user):
        return self.members.filter(user=user).exists() or self.leader == user

    def can_join(self, user):
        if self.status == "attended":
            return False, "Cannot join a team that has attended the event"

        if self.is_member(user):
            return False, "You are already a member of this team"

        if InPersonMember.objects.filter(user=user).exclude(team__status="disbanded").exists():
            return False, "You are already a member of another in-person team"

        if InPersonTeam.objects.filter(leader=user).exclude(status="disbanded").exists():
            return False, "You are leader of another team"

        return True, "Can join"


class InPersonMember(models.Model):
    """Member of an in-person team"""

    team = models.ForeignKey(InPersonTeam, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inperson_memberships")
    has_paid = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["team", "user"]]
        ordering = ["joined_at"]
        verbose_name = "In-Person Team Member"
        verbose_name_plural = "In-Person Team Members"

    def __str__(self):
        return f"{self.user.email} in {self.team.name}"

    def save(self, *args, **kwargs):
        # Check if user is already in another team
        if not self.pk:
            can_join, message = self.team.can_join(self.user)
            if not can_join:
                raise ValidationError(message)
        super().save(*args, **kwargs)

        # Auto-activate team if it reaches minimum members (3)
        if self.team.member_count >= MIN_MEMBERS_PER_TEAM and self.team.status == "incomplete":
            self.team.activate()

    def delete(self, *args, **kwargs):
        team = self.team
        super().delete(*args, **kwargs)

        # Mark team as incomplete if it drops below minimum
        if team.member_count < MIN_MEMBERS_PER_TEAM and team.status in ["active", "attended"]:
            team.status = "incomplete"
            team.save(update_fields=["status"])


class InPersonSubmission(models.Model):
    """Submission for each phase of in-person competition"""

    PHASE_CHOICES = [
        (0, "Phase 0: Introduction"),
        (2, "Phase 2: Development"),
        (3, "Phase 3: Polish"),
        (4, "Phase 4: Final Battle"),
    ]

    team = models.ForeignKey(InPersonTeam, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inperson_submissions",
    )
    phase = models.IntegerField(choices=PHASE_CHOICES)
    content = models.TextField()

    # Judging
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    judge_notes = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["team", "phase"]]
        ordering = ["team", "phase"]
        verbose_name = "In-Person Submission"
        verbose_name_plural = "In-Person Submissions"

    def __str__(self):
        return f"{self.team.name} - Phase {self.phase}"
