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
    ]

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
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

    @property
    def member_count(self):
        return self.members.count() + 1

    def can_join(self, user):
        if self.leader == user:
            return False, "Leader is already part of the team"
        if self.members.filter(user=user).exists():
            return False, "You are already a member of this team"
        if OnlineMember.objects.filter(user=user).exclude(team__status="inactive").exists():
            return False, "You are already a member of another team"
        if self.member_count >= MAX_MEMBERS:
            return False, "Team is full"
        return True, "Can join"

    def mark_completed_if_needed(self):
        if self.status == "active" and self.members.exists():
            self.status = "completed"
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
        super().delete(*args, **kwargs)
