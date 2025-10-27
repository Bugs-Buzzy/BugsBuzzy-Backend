from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import random
import string

User = get_user_model()


MIN_MEMBERS = 2
MAX_MEMBERS = 6


class OnlineTeam(models.Model):
    STATUS_CHOICES = [
        ("inactive", "Inactive"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("attended", "Attended"),
    ]

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    avatar = models.TextField(
        blank=True,
        help_text="Base64 data URI for team avatar (max 256x256)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="led_gamejam_teams")
    invite_code = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (Leader: {self.leader.email})"

    def generate_invite_code(self):
        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not OnlineTeam.objects.filter(invite_code=code).exists():
                return code

    def activate(self):
        if self.status == "inactive":
            self.status = "active"
            if not self.invite_code:
                self.invite_code = self.generate_invite_code()
            self.save(update_fields=["status", "invite_code", "updated_at"])
    
    def mark_attended(self):
        """Mark team as attended"""
        self.status = "attended"
        self.save(update_fields=["status"]) 

    @property
    def member_count(self):
        return self.members.count() + 1

    def can_join(self, user):
        if self.status == "attended":
            return False, "Cannot join a team that has attended the event"
        if self.leader == user:
            return False, "Leader is already part of the team"
        if self.members.filter(user=user).exists():
            return False, "You are already a member of this team"
        if OnlineMember.objects.filter(user=user).exists():
            return False, "You are already a member of another team"
        if OnlineTeam.objects.filter(leader=user).exists():
            return False, "You are leader of another team"
        if self.member_count >= MAX_MEMBERS:
            return False, "Team is full"
        return True, "Can join"

    def mark_completed_if_needed(self):
        # Only update status if team is active or completed (not attended)
        if self.status in ["active", "completed"]:
            if self.member_count >= MIN_MEMBERS and self.status != "completed":
                self.status = "completed"
                self.save(update_fields=["status"])
            elif self.member_count < MIN_MEMBERS and self.status == "completed":
                # Downgrade from completed to active if members drop below minimum
                self.status = "active"
                self.save(update_fields=["status"])


class OnlineMember(models.Model):
    team = models.ForeignKey(OnlineTeam, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gamejam_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["team", "user"]]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.email} in {self.team.name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            can_join, message = self.team.can_join(self.user)
            if not can_join:
                raise ValidationError(message)
        super().save(*args, **kwargs)
        self.team.mark_completed_if_needed()

    def delete(self, *args, **kwargs):
        team = self.team
        super().delete(*args, **kwargs)
        # Update team status after member deletion
        team.mark_completed_if_needed()


class OnlineCompetition(models.Model):
    """Singleton model to control the single online competition phase."""

    phase_active = models.BooleanField(default=False, verbose_name="Online Phase Active")
    title = models.CharField(max_length=200, default="Online Phase", blank=True)
    description = models.TextField(blank=True, null=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Online Competition Settings"
        verbose_name_plural = "Online Competition Settings"

    def save(self, *args, **kwargs):
        # enforce a single row
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Online Competition Settings"


class OnlineSubmission(models.Model):
    """Submission model for the single online phase."""

    team = models.ForeignKey(OnlineTeam, on_delete=models.CASCADE, related_name="submissions")

    # Content
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="online/submissions/", null=True, blank=True)
    game_url = models.URLField(blank=True)

    # Judging
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    judge_notes = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["team"]]
        ordering = ["team"]
        verbose_name = "Online Submission"
        verbose_name_plural = "Online Submissions"

    def __str__(self):
        return f"{self.team.name} - Online Submission"

