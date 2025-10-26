from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from .models import OnlineTeam, OnlineMember
from .serializers import OnlineTeamSerializer, OnlineMemberSerializer


class MyTeamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        team = OnlineTeam.objects.filter(leader=request.user).first()
        if not team:
            membership = OnlineMember.objects.filter(user=request.user).select_related("team").first()
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
            return Response({"error": "You already have a gamejam team"}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            team = OnlineTeam.objects.create(name=name, description=description, leader=request.user)
            serializer = OnlineTeamSerializer(team, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        if not invite_code:
            return Response({"error": "Invite code is required"}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({"error": "Team leader cannot leave"}, status=status.HTTP_400_BAD_REQUEST)

        membership = OnlineMember.objects.filter(user=request.user, team=team).first()
        if not membership:
            return Response({"error": "You are not a member of this team"}, status=status.HTTP_404_NOT_FOUND)

        membership.delete()
        return Response({"message": "Left team successfully"})
