from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class BaseTeam(models.Model):
    """
    Abstract base team model with shared logic for both in-person and online teams.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("disbanded", "Disbanded"),
    ]

    # Basic team information
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Team identification
    invite_code = models.CharField(max_length=8, unique=True, editable=False)

    # Team leader (creator)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_teams")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.__class__.__name__})"

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    def generate_invite_code(self):
        """Generate a unique 8-character invite code."""
        import random
        import string

        while True:
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not self.__class__.objects.filter(invite_code=code).exists():
                return code

    def get_members(self):
        """Get all team members including the leader."""
        filters = {}
        if isinstance(self, InPersonTeam):
            filters["in_person_team"] = self
        elif isinstance(self, OnlineTeam):
            filters["online_team"] = self
        return TeamMember.objects.filter(**filters).select_related("user")

    def get_member_count(self):
        """Get the total number of team members."""
        return self.get_members().count()

    def is_member(self, user):
        """Check if a user is a member of this team."""
        filters = {"user": user}
        if isinstance(self, InPersonTeam):
            filters["in_person_team"] = self
        elif isinstance(self, OnlineTeam):
            filters["online_team"] = self
        return TeamMember.objects.filter(**filters).exists()

    def can_join(self, user):
        """Check if a user can join this team."""
        if self.is_member(user):
            return False, "You are already a member of this team"

        # User can't join if they're already a member of another team of this type
        if self.__class__.__name__ == "InPersonTeam":
            if TeamMember.objects.filter(user=user, in_person_team__status="active").exists():
                return False, "You are already a member of another in-person team"
        elif self.__class__.__name__ == "OnlineTeam":
            if TeamMember.objects.filter(user=user, online_team__status="active").exists():
                return False, "You are already a member of another online team"

        return True, "Can join"

    def disband(self):
        """Disband the team."""
        self.status = "disbanded"
        self.save()


class InPersonTeam(BaseTeam):
    """
    In-person team where each member pays individually.
    Team is qualified when ALL members have paid.
    """

    class Meta:
        unique_together = ["leader"]


class OnlineTeam(BaseTeam):
    """
    Online team where one payment covers the entire team.
    Team is qualified when ANY member pays for the whole team.
    """

    class Meta:
        unique_together = ["leader"]


class TeamMember(models.Model):
    """
    Model to track team members.
    Simple model with two optional foreign keys - one for in-person teams, one for online teams.
    """

    # Two optional foreign keys - only one should be set
    in_person_team = models.ForeignKey(
        InPersonTeam, on_delete=models.CASCADE, null=True, blank=True, related_name="members"
    )
    online_team = models.ForeignKey(
        OnlineTeam, on_delete=models.CASCADE, null=True, blank=True, related_name="members"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")

    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["in_person_team", "user"], ["online_team", "user"]]
        ordering = ["joined_at"]

    def __str__(self):
        team_name = "Unknown Team"
        if self.in_person_team:
            team_name = self.in_person_team.name
        elif self.online_team:
            team_name = self.online_team.name
        return f"{self.user.email} in {team_name}"

    def save(self, *args, **kwargs):
        # Validate that exactly one team is set
        if not (bool(self.in_person_team) ^ bool(self.online_team)):
            raise ValidationError("Exactly one team (in_person_team or online_team) must be set")

        # Validate that user can join this team
        team = self.in_person_team or self.online_team
        if team:
            can_join, message = team.can_join(self.user)
            if not can_join:
                raise ValidationError(message)

        super().save(*args, **kwargs)
