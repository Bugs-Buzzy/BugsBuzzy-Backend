from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from accounts.permissions import HasPurchased
from .models import InPersonTeam, InPersonMember, InPersonCompetition, InPersonSubmission
from .serializers import (
    InPersonTeamSerializer,
    InPersonMemberSerializer,
    InPersonCompetitionSerializer,
    InPersonSubmissionSerializer,
)


class CompetitionStatusView(APIView):
    """Get current competition phase status"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        comp = InPersonCompetition.get_solo()
        serializer = InPersonCompetitionSerializer(comp)
        return Response(serializer.data)


class MyTeamView(APIView):
    """Get user's team"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user is leader (any non-disbanded team)
        team = InPersonTeam.objects.filter(leader=request.user).exclude(status="disbanded").first()

        # Check if user is member
        if not team:
            membership = (
                InPersonMember.objects.filter(user=request.user)
                .exclude(team__status="disbanded")
                .select_related("team")
                .first()
            )
            if membership:
                team = membership.team

        if team:
            serializer = InPersonTeamSerializer(team, context={"request": request})
            return Response({"team": serializer.data})

        return Response({"team": None})


class TeamCreateView(APIView):
    """Create a new team"""

    permission_classes = [permissions.IsAuthenticated, HasPurchased("inperson")]

    def post(self, request):
        # Check if already has team (any non-disbanded)
        if InPersonTeam.objects.filter(leader=request.user).exclude(status="disbanded").exists():
            return Response(
                {"error": "You already have an active team"}, status=status.HTTP_400_BAD_REQUEST
            )

        if (
            InPersonMember.objects.filter(user=request.user)
            .exclude(team__status="disbanded")
            .exists()
        ):
            return Response(
                {"error": "You are already a member of another team"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = request.data.get("name")
        description = request.data.get("description", "")
        avatar = request.data.get("avatar", "")

        if not name:
            return Response({"error": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            team = InPersonTeam.objects.create(
                name=name, description=description, avatar=avatar, leader=request.user
            )

            # Check if team should be activated (leader count = 1, so need 2 more members minimum)
            # Since only leader exists, team stays incomplete

            serializer = InPersonTeamSerializer(team, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamJoinView(APIView):
    """Join a team with invite code"""

    permission_classes = [permissions.IsAuthenticated, HasPurchased("inperson")]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        if not invite_code:
            return Response(
                {"error": "Invite code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = InPersonTeam.objects.exclude(status="disbanded").get(invite_code=invite_code)
        except InPersonTeam.DoesNotExist:
            return Response({"error": "Invalid invite code"}, status=status.HTTP_404_NOT_FOUND)

        can_join, message = team.can_join(request.user)
        if not can_join:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            InPersonMember.objects.create(user=request.user, team=team)
            # Member.save() will auto-activate team if needed
            team.refresh_from_db()  # Refresh to get updated status
            serializer = InPersonTeamSerializer(team, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamLeaveView(APIView):
    """Leave team"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id)

        if team.leader == request.user:
            return Response(
                {"error": "Team leader cannot leave. Disband team instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent leaving if team has attended
        if team.status == "attended":
            return Response(
                {"error": "Cannot leave a team that has attended the event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = InPersonMember.objects.filter(user=request.user, team=team).first()
        if not membership:
            return Response(
                {"error": "You are not a member of this team"}, status=status.HTTP_404_NOT_FOUND
            )

        membership.delete()
        # Member.delete() will auto-update team status if needed
        return Response({"message": "Left team successfully"})


class TeamDisbandView(APIView):
    """Disband team (leader only)"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)

        # Prevent disbanding if team has attended
        if team.status == "attended":
            return Response(
                {"error": "Cannot disband a team that has attended the event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team.disband()
        return Response({"message": "Team disbanded successfully"})


class TeamInviteCodeRevokeView(APIView):
    """Revoke and regenerate invite code (leader only)"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)
        team.revoke_invite_code()
        serializer = InPersonTeamSerializer(team, context={"request": request})
        return Response(
            {
                "message": "Invite code revoked and regenerated",
                "new_invite_code": team.invite_code,
                "team": serializer.data,
            }
        )


class TeamUpdateView(APIView):
    """Update team info (leader only)"""

    permission_classes = [permissions.IsAuthenticated]

    def _update_team(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)

        # Prevent editing if team has attended
        if team.status == "attended":
            return Response(
                {"error": "Cannot edit a team that has attended the event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "name" in request.data:
            team.name = request.data["name"]
        if "description" in request.data:
            team.description = request.data["description"]
        if "avatar" in request.data:
            team.avatar = request.data["avatar"]

        team.save()
        serializer = InPersonTeamSerializer(team, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, team_id):
        return self._update_team(request, team_id)

    def put(self, request, team_id):
        return self._update_team(request, team_id)


class TeamMembersView(APIView):
    """Get team members"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, team_id):
        team = get_object_or_404(InPersonTeam.objects.exclude(status="disbanded"), id=team_id)

        if not team.is_member(request.user):
            return Response(
                {"error": "You are not a member of this team"}, status=status.HTTP_403_FORBIDDEN
            )

        members = InPersonMember.objects.filter(team=team).select_related("user")
        serializer = InPersonMemberSerializer(members, many=True)
        return Response(serializer.data)


class SubmissionCreateView(APIView):
    """Submit for a phase"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Get user's team
        team = InPersonTeam.objects.filter(leader=request.user).exclude(status="disbanded").first()
        if not team:
            membership = (
                InPersonMember.objects.filter(user=request.user)
                .exclude(team__status="disbanded")
                .select_related("team")
                .first()
            )
            if membership:
                team = membership.team

        if not team:
            return Response(
                {"error": "You are not in an active team"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Team must be active or attended to submit
        if team.status not in ["active", "attended"]:
            return Response(
                {"error": "Your team must be complete to submit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_phase = request.data.get("phase")
        content = request.data.get("content", "").strip()

        if raw_phase is None:
            return Response({"error": "Phase is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phase = int(raw_phase)
        except (TypeError, ValueError):
            return Response({"error": "Phase must be a number"}, status=status.HTTP_400_BAD_REQUEST)

        allowed_phases = {0, 2, 4}
        if phase not in allowed_phases:
            return Response(
                {"error": "Submissions are only allowed for phases 0, 2, and 4"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)

        comp = InPersonCompetition.get_solo()

        # Check if phase is active
        phase_active = getattr(comp, f"phase_{phase}_active", False)
        if not phase_active:
            return Response(
                {"error": f"Phase {phase} is not active yet"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create a new submission and mark it as the final one for this team+phase.
        with db_transaction.atomic():
            # Mark previous submissions (if any) as not final
            InPersonSubmission.objects.filter(team=team, phase=phase, is_final=True).update(
                is_final=False
            )

            submission = InPersonSubmission.objects.create(
                team=team,
                phase=phase,
                content=content,
                submitted_by=request.user,
                is_final=True,
            )

            # Mark team as attended after first submission
            if team.status == "active":
                team.mark_attended()

        serializer = InPersonSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubmissionListView(APIView):
    """Get team's submissions"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get user's team (any non-disbanded)
        team = InPersonTeam.objects.filter(leader=request.user).exclude(status="disbanded").first()
        if not team:
            membership = (
                InPersonMember.objects.filter(user=request.user)
                .exclude(team__status="disbanded")
                .select_related("team")
                .first()
            )
            if membership:
                team = membership.team

        if not team:
            return Response({"submissions": []})

        submissions = InPersonSubmission.objects.filter(team=team)
        serializer = InPersonSubmissionSerializer(submissions, many=True)
        return Response({"submissions": serializer.data})


class VerifyTeamCodeView(APIView):
    """Verify team upload code for uploader service (no authentication required)"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        upload_code = request.data.get("code")

        if not upload_code:
            return Response(
                {"error": "Team auth code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = InPersonTeam.objects.get(invite_code=upload_code)
        except InPersonTeam.DoesNotExist:
            return Response({"error": "Invalid team auth code"}, status=status.HTTP_404_NOT_FOUND)

        # Only attended teams can use the uploader
        if team.status != "attended":
            return Response(
                {"error": "This team has not attended the event yet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Return minimal team info for display
        return Response(
            {
                "valid": True,
                "team": {
                    "id": team.id,
                    "name": team.name,
                    "leader": {
                        "email": team.leader.email,
                        "first_name": team.leader.first_name,
                        "last_name": team.leader.last_name,
                    },
                    "member_count": team.member_count,
                },
            },
            status=status.HTTP_200_OK,
        )
