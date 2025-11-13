from rest_framework import serializers
from django.contrib.auth import get_user_model
from typing import List, Dict, Any
from .models import InPersonTeam, InPersonMember, InPersonCompetition, InPersonSubmission

User = get_user_model()


class InPersonUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class InPersonMemberSerializer(serializers.ModelSerializer):
    user = InPersonUserSerializer(read_only=True)
    has_paid = serializers.SerializerMethodField()

    class Meta:
        model = InPersonMember
        fields = ["id", "user", "has_paid", "joined_at"]

    def get_has_paid(self, obj: InPersonMember) -> bool:
        return obj.user.has_paid


class InPersonTeamSerializer(serializers.ModelSerializer):
    leader = InPersonUserSerializer(read_only=True)
    members = InPersonMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    is_leader = serializers.SerializerMethodField()

    class Meta:
        model = InPersonTeam
        fields = [
            "id",
            "name",
            "team_number",
            "description",
            "avatar",
            "status",
            "invite_code",
            "leader",
            "members",
            "member_count",
            "is_leader",
            "created_at",
        ]
        read_only_fields = ["invite_code", "team_number", "created_at"]

    def get_member_count(self, obj: InPersonTeam) -> int:
        return obj.member_count

    def get_is_leader(self, obj: InPersonTeam) -> bool:
        request = self.context.get("request")
        return request and request.user == obj.leader


class InPersonSubmissionSerializer(serializers.ModelSerializer):
    team = InPersonTeamSerializer(read_only=True)
    submitted_by = InPersonUserSerializer(read_only=True)
    is_final = serializers.BooleanField(read_only=True)

    class Meta:
        model = InPersonSubmission
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

    read_only_fields = [
        "submitted_at",
        "updated_at",
        "score",
        "judge_notes",
        "submitted_by",
        "team",
        "is_final",
    ]


class InPersonCompetitionSerializer(serializers.ModelSerializer):
    phases = serializers.SerializerMethodField()

    class Meta:
        model = InPersonCompetition
        fields = ["phases"]

    def get_phases(self, obj: InPersonCompetition) -> List[Dict[str, Any]]:
        return [
            {
                "id": 0,
                "active": obj.phase_0_active,
                "title": obj.phase_0_title,
                "description": obj.phase_0_description,
                "start": obj.phase_0_start,
                "end": obj.phase_0_end,
            },
            {
                "id": 1,
                "active": obj.phase_1_active,
                "title": obj.phase_1_title,
                "description": obj.phase_1_description,
                "start": obj.phase_1_start,
                "end": obj.phase_1_end,
            },
            {
                "id": 2,
                "active": obj.phase_2_active,
                "title": obj.phase_2_title,
                "description": obj.phase_2_description,
                "start": obj.phase_2_start,
                "end": obj.phase_2_end,
            },
            {
                "id": 3,
                "active": obj.phase_3_active,
                "title": obj.phase_3_title,
                "description": obj.phase_3_description,
                "start": obj.phase_3_start,
                "end": obj.phase_3_end,
            },
            {
                "id": 4,
                "active": obj.phase_4_active,
                "title": obj.phase_4_title,
                "description": obj.phase_4_description,
                "start": obj.phase_4_start,
                "end": obj.phase_4_end,
            },
        ]


class InPersonTeamCreateSerializer(serializers.Serializer):
    """Serializer for creating a team"""
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class InPersonTeamJoinSerializer(serializers.Serializer):
    """Serializer for joining a team"""
    invite_code = serializers.CharField(required=True)


class InPersonTeamUpdateSerializer(serializers.Serializer):
    """Serializer for updating team info"""
    name = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_blank=True)


class InPersonVerifyTeamCodeSerializer(serializers.Serializer):
    """Serializer for verifying team code"""
    code = serializers.CharField(required=True)


class InPersonSubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a submission"""
    phase = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)


class TeamNumberSerializer(serializers.Serializer):
    """Serializer for getting team by number"""
    team_number = serializers.IntegerField(required=True)
