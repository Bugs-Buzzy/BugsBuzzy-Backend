from rest_framework import serializers
from .models import OnlineTeam, OnlineMember, OnlineSubmission, OnlineCompetition
from django.contrib.auth import get_user_model

User = get_user_model()


class OnlineUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class OnlineMemberSerializer(serializers.ModelSerializer):
    user = OnlineUserSerializer(read_only=True)

    class Meta:
        model = OnlineMember
        fields = ["id", "user", "joined_at"]


class OnlineTeamSerializer(serializers.ModelSerializer):
    leader = OnlineUserSerializer(read_only=True)
    members = OnlineMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = OnlineTeam
        fields = [
            "id",
            "name",
            "team_number",
            "description",
            "avatar",
            "status",
            "leader",
            "invite_code",
            "members",
            "member_count",
            "created_at",
        ]
        read_only_fields = ["invite_code", "status", "created_at", "team_number"]

    def get_member_count(self, obj: OnlineTeam) -> int:
        return obj.member_count


class OnlineSubmissionSerializer(serializers.ModelSerializer):
    team = OnlineTeamSerializer(read_only=True)
    submitted_by = OnlineUserSerializer(read_only=True)
    is_final = serializers.BooleanField(read_only=True)

    class Meta:
        model = OnlineSubmission
        fields = [
            "id",
            "team",
            "submitted_by",
            "phase",
            "is_final",
            "content",
            "score",
            "judge_notes",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = ["submitted_at", "updated_at", "score", "judge_notes"]


class OnlineCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineCompetition
        fields = ["phase_active", "title", "description", "start", "end"]


class OnlineTeamCreateSerializer(serializers.Serializer):
    """Serializer for creating a team"""
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class OnlineTeamJoinSerializer(serializers.Serializer):
    """Serializer for joining a team"""
    invite_code = serializers.CharField(required=True)


class OnlineTeamUpdateSerializer(serializers.Serializer):
    """Serializer for updating team info"""
    name = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_blank=True)


class OnlineVerifyTeamCodeSerializer(serializers.Serializer):
    """Serializer for verifying team code"""
    code = serializers.CharField(required=True)


class OnlineSubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a submission"""
    phase = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)
