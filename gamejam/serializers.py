from rest_framework import serializers
from .models import OnlineTeam, OnlineMember, OnlineSubmission, OnlineCompetition
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class OnlineMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OnlineMember
        fields = ["id", "user", "joined_at"]


class OnlineTeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    members = OnlineMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = OnlineTeam
        fields = [
            "id",
            "name",
            "description",
            "avatar",
            "status",
            "leader",
            "invite_code",
            "members",
            "member_count",
            "created_at",
        ]
        read_only_fields = ["invite_code", "status", "created_at"]

    def get_member_count(self, obj):
        return obj.member_count


class OnlineSubmissionSerializer(serializers.ModelSerializer):
    team = OnlineTeamSerializer(read_only=True)

    class Meta:
        model = OnlineSubmission
        fields = [
            "id",
            "team",
            "title",
            "description",
            "file",
            "game_url",
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
