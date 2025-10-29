from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import InPersonTeam, InPersonMember, InPersonCompetition, InPersonSubmission

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class InPersonMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    has_paid = serializers.SerializerMethodField()

    class Meta:
        model = InPersonMember
        fields = ["id", "user", "has_paid", "joined_at"]

    def get_has_paid(self, obj):
        return obj.user.has_paid


class InPersonTeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    members = InPersonMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    is_leader = serializers.SerializerMethodField()

    class Meta:
        model = InPersonTeam
        fields = [
            "id",
            "name",
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
        read_only_fields = ["invite_code", "created_at"]

    def get_member_count(self, obj):
        return obj.member_count

    def get_is_leader(self, obj):
        request = self.context.get("request")
        return request and request.user == obj.leader


class InPersonSubmissionSerializer(serializers.ModelSerializer):
    team = InPersonTeamSerializer(read_only=True)
    submitted_by = UserSerializer(read_only=True)
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
    read_only_fields = ["submitted_at", "updated_at", "score", "judge_notes", "submitted_by", "team", "is_final"]


class InPersonCompetitionSerializer(serializers.ModelSerializer):
    phases = serializers.SerializerMethodField()

    class Meta:
        model = InPersonCompetition
        fields = ["phases"]

    def get_phases(self, obj):
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
