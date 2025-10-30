from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from .models import OnlineTeam, OnlineMember
from .serializers import OnlineTeamSerializer, OnlineMemberSerializer
from .models import OnlineCompetition, OnlineSubmission
from .serializers import OnlineCompetitionSerializer, OnlineSubmissionSerializer


class CompetitionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        comp = OnlineCompetition.get_solo()
        serializer = OnlineCompetitionSerializer(comp)
        return Response(serializer.data)


class SubmissionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # find the user's team
        team = OnlineTeam.objects.filter(leader=request.user).first()
        if not team:
            membership = (
                OnlineMember.objects.filter(user=request.user).select_related("team").first()
            )
            if membership:
                team = membership.team

        if not team:
            return Response(
                {"error": "You are not in an active team"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Team must be completed (reached MIN_MEMBERS) or attended to submit
        if team.status not in ["completed", "attended"]:
            return Response(
                {"error": "Your team must be complete to submit"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comp = OnlineCompetition.get_solo()
        if not comp.phase_active:
            return Response(
                {"error": "Online competition phase is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        title = request.data.get("title", "")
        description = request.data.get("description", "")
        game_url = request.data.get("game_url", "")
        file = request.FILES.get("file")

        submission, created = OnlineSubmission.objects.update_or_create(
            team=team,
            defaults={
                "title": title,
                "description": description,
                "game_url": game_url,
                "file": file,
            },
        )

        # Mark team as attended after first submission
        if created and team.status == "completed":
            team.mark_attended()

        serializer = OnlineSubmissionSerializer(submission)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class SubmissionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        team = OnlineTeam.objects.filter(leader=request.user).first()
        if not team:
            membership = (
                OnlineMember.objects.filter(user=request.user).select_related("team").first()
            )
            if membership:
                team = membership.team

        if not team:
            return Response({"submissions": []})

        submissions = OnlineSubmission.objects.filter(team=team)
        serializer = OnlineSubmissionSerializer(submissions, many=True)
        return Response({"submissions": serializer.data})


class MyTeamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        team = OnlineTeam.objects.filter(leader=request.user).first()
        if not team:
            membership = (
                OnlineMember.objects.filter(user=request.user).select_related("team").first()
            )
            if membership:
                team = membership.team

        if not team:
            return Response({"team": None})

        serializer = OnlineTeamSerializer(team, context={"request": request})
        return Response({"team": serializer.data})


class TeamCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        description = request.data.get("description", "")

        if not name:
            return Response({"error": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST)

        if OnlineTeam.objects.filter(leader=request.user).exists():
            return Response(
                {"error": "You already have a gamejam team"}, status=status.HTTP_400_BAD_REQUEST
            )

        if OnlineMember.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You are already a member of another team"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with db_transaction.atomic():
            team = OnlineTeam.objects.create(
                name=name, description=description, leader=request.user
            )
            serializer = OnlineTeamSerializer(team, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        if not invite_code:
            return Response(
                {"error": "Invite code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = OnlineTeam.objects.get(invite_code=invite_code)
        except OnlineTeam.DoesNotExist:
            return Response({"error": "Invalid invite code"}, status=status.HTTP_404_NOT_FOUND)

        can_join, message = team.can_join(request.user)
        if not can_join:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            OnlineMember.objects.create(user=request.user, team=team)
            team.refresh_from_db()
            serializer = OnlineTeamSerializer(team, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(OnlineTeam, id=team_id)

        if team.leader == request.user:
            return Response(
                {"error": "Team leader cannot leave the team"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent leaving if team has attended
        if team.status == "attended":
            return Response(
                {"error": "Cannot leave a team that has attended the event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = OnlineMember.objects.filter(user=request.user, team=team).first()
        if not membership:
            return Response(
                {"error": "You are not a member of this team"}, status=status.HTTP_404_NOT_FOUND
            )

        membership.delete()
        # OnlineMember.delete() will trigger mark_completed_if_needed() to update status
        return Response({"message": "Left team successfully"})


class TeamUpdateView(APIView):
    """Update team info (leader only)"""

    permission_classes = [permissions.IsAuthenticated]

    def _update_team(self, request, team_id):
        team = get_object_or_404(OnlineTeam, id=team_id, leader=request.user)

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
        serializer = OnlineTeamSerializer(team, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, team_id):
        return self._update_team(request, team_id)

    def put(self, request, team_id):
        return self._update_team(request, team_id)


class TeamDeleteView(APIView):
    """Delete inactive team (leader only, before payment)"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, team_id):
        team = get_object_or_404(OnlineTeam, id=team_id, leader=request.user)

        # Only allow deletion of inactive teams (before payment)
        if team.status != "inactive":
            return Response(
                {"error": "Only inactive teams can be deleted. Team has already been activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete the team completely
        team.delete()
        return Response({"message": "Team deleted successfully"})


class TeamActivateView(APIView):
    """Activate team after payment (leader only)"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(OnlineTeam, id=team_id, leader=request.user)

        if team.status != "inactive":
            return Response({"error": "Team already activated"}, status=status.HTTP_400_BAD_REQUEST)

        team.activate()
        serializer = OnlineTeamSerializer(team, context={"request": request})
        return Response(serializer.data)


class VerifyTeamCodeView(APIView):
    """Verify team upload code for uploader service (no authentication required)"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        upload_code = request.data.get("code")
        
        if not upload_code:
            return Response(
                {"error": "Team Auth code is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = OnlineTeam.objects.get(invite_code=upload_code)
        except OnlineTeam.DoesNotExist:
            return Response(
                {"error": "Invalid team auth code"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Only attended teams can use the uploader
        if team.status != "attended":
            return Response(
                {"error": "This team has not attended the event yet"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Return minimal team info for display
        return Response({
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
            }
        }, status=status.HTTP_200_OK)
