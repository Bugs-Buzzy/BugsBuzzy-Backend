from rest_framework import generics, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.contrib.auth import get_user_model
from accounts.permissions import HasPaid

from .models import InPersonTeam, OnlineTeam, TeamMember
from .serializers import (
    InPersonTeamSerializer, OnlineTeamSerializer, TeamCreateSerializer, 
    TeamMemberSerializer
)

User = get_user_model()



class AllTeamsView(APIView):
    """Get all teams (both in-person and online) in a unified format."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all teams where user is leader or member
        in_person_teams = InPersonTeam.objects.filter(
            models.Q(leader=user) | models.Q(members__user=user),
            status='active'
        ).distinct()
        
        online_teams = OnlineTeam.objects.filter(
            models.Q(leader=user) | models.Q(members__user=user),
            status='active'
        ).distinct()
        
        # Serialize both types
        in_person_data = InPersonTeamSerializer(in_person_teams, many=True, context={'request': request}).data
        online_data = OnlineTeamSerializer(online_teams, many=True, context={'request': request}).data
        
        # Combine all teams into a single list
        all_teams = in_person_data + online_data
        
        # Sort by creation date (newest first)
        all_teams.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response({
            'teams': all_teams,
            'total_count': len(all_teams),
            'in_person_count': len(in_person_data),
            'online_count': len(online_data),
            'in_person_ids': [team['id'] for team in in_person_data],
            'online_ids': [team['id'] for team in online_data],
            'in_person_names': [team['name'] for team in in_person_data],
            'online_names': [team['name'] for team in online_data]
        })


class InPersonTeamDetailView(generics.RetrieveAPIView):
    """Get in-person team details."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InPersonTeamSerializer
    
    def get_queryset(self):
        user = self.request.user
        return InPersonTeam.objects.filter(
            models.Q(leader=user) | models.Q(members__user=user),
            status='active'
        ).distinct()


class OnlineTeamDetailView(generics.RetrieveAPIView):
    """Get online team details."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OnlineTeamSerializer
    
    def get_queryset(self):
        user = self.request.user
        return OnlineTeam.objects.filter(
            models.Q(leader=user) | models.Q(members__user=user),
            status='active'
        ).distinct()


class InPersonTeamJoinView(APIView):
    """Join an in-person team using invite code."""
    permission_classes = [permissions.IsAuthenticated, HasPaid]
    
    def post(self, request):
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({
                'error': 'Invite code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            team = InPersonTeam.objects.get(invite_code=invite_code, status='active')
        except InPersonTeam.DoesNotExist:
            return Response({
                'error': 'Invalid invite code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user can join
        can_join, message = team.can_join(request.user)
        if not can_join:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Create team member
            team_member = TeamMember.objects.create(
                user=request.user,
                in_person_team=team
            )
            team_serializer = InPersonTeamSerializer(team, context={'request': request})
            
            return Response({
                'message': 'Successfully joined the in-person team',
                'team': team_serializer.data
            }, status=status.HTTP_201_CREATED)


class OnlineTeamJoinView(APIView):
    """Join an online team using invite code."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({
                'error': 'Invite code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            team = OnlineTeam.objects.get(invite_code=invite_code, status='active')
        except OnlineTeam.DoesNotExist:
            return Response({
                'error': 'Invalid invite code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user can join
        can_join, message = team.can_join(request.user)
        if not can_join:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Create team member
            team_member = TeamMember.objects.create(
                user=request.user,
                online_team=team
            )
            team_serializer = OnlineTeamSerializer(team, context={'request': request})
            
            return Response({
                'message': 'Successfully joined the online team',
                'team': team_serializer.data
            }, status=status.HTTP_201_CREATED)


class InPersonTeamMembersView(generics.ListAPIView):
    """List in-person team members."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamMemberSerializer
    
    def get_queryset(self):
        team_id = self.kwargs['team_id']
        
        # Get the in-person team
        team = get_object_or_404(InPersonTeam, id=team_id, status='active')
        
        # Check if user is a member or leader
        if not (team.leader == self.request.user or team.is_member(self.request.user)):
            raise PermissionDenied("You are not a member of this team")
        
        return TeamMember.objects.filter(in_person_team=team)


class OnlineTeamMembersView(generics.ListAPIView):
    """List online team members."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeamMemberSerializer
    
    def get_queryset(self):
        team_id = self.kwargs['team_id']
        
        # Get the online team
        team = get_object_or_404(OnlineTeam, id=team_id, status='active')
        
        # Check if user is a member or leader
        if not (team.leader == self.request.user or team.is_member(self.request.user)):
            raise PermissionDenied("You are not a member of this team")
        
        return TeamMember.objects.filter(online_team=team)


class InPersonTeamCreateView(APIView):
    """Create a new in-person team."""
    permission_classes = [permissions.IsAuthenticated, HasPaid]
    
    def post(self, request):
        # Check if user already has an active in-person team
        if InPersonTeam.objects.filter(leader=request.user, status='active').exists():
            return Response({
                'error': 'You already have an active in-person team'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is already a member of another in-person team
        if TeamMember.objects.filter(
            user=request.user, 
            in_person_team__status='active'
        ).exists():
            return Response({
                'error': 'You are already a member of another in-person team'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name')
        description = request.data.get('description', '')
        
        if not name:
            return Response({
                'error': 'Team name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            team = InPersonTeam.objects.create(
                name=name,
                description=description,
                leader=request.user
            )
            team_member = TeamMember.objects.create(
                user=request.user,
                in_person_team=team
            )
            team_serializer = InPersonTeamSerializer(team, context={'request': request})
            
            return Response({
                'message': 'In-person team created successfully',
                'team': team_serializer.data
            }, status=status.HTTP_201_CREATED)


class OnlineTeamCreateView(APIView):
    """Create a new online team."""
    permission_classes = [permissions.IsAuthenticated, HasPaid]
    
    def post(self, request):
        # Check if user already has an active online team
        if OnlineTeam.objects.filter(leader=request.user, status='active').exists():
            return Response({
                'error': 'You already have an active online team'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is already a member of another online team
        if TeamMember.objects.filter(
            user=request.user, 
            online_team__status='active'
        ).exists():
            return Response({
                'error': 'You are already a member of another online team'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name')
        description = request.data.get('description', '')
        
        if not name:
            return Response({
                'error': 'Team name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            team = OnlineTeam.objects.create(
                name=name,
                description=description,
                leader=request.user
            )
            team_member = TeamMember.objects.create(
                user=request.user,
                online_team=team
            )
            team_serializer = OnlineTeamSerializer(team, context={'request': request})
            
            return Response({
                'message': 'Online team created successfully',
                'team': team_serializer.data
            }, status=status.HTTP_201_CREATED)


class InPersonTeamLeaveView(APIView):
    """Leave an in-person team."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, team_id):
        try:
            team = InPersonTeam.objects.get(id=team_id, status='active')
        except InPersonTeam.DoesNotExist:
            return Response({
                'error': 'In-person team not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if team.leader == request.user:
            team.delete()
            return Response({
                'message': 'Successfully deleted team'
            }, status=status.HTTP_200_OK)
        
        try:
            team_member = TeamMember.objects.get(in_person_team=team, user=request.user)
            team_member.delete()
            return Response({
                'message': 'Successfully left the in-person team'
            }, status=status.HTTP_200_OK)
        except TeamMember.DoesNotExist:
            return Response({
                'error': 'You are not a member of this in-person team'
            }, status=status.HTTP_400_BAD_REQUEST)


class OnlineTeamLeaveView(APIView):
    """Leave an online team."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, team_id):
        try:
            team = OnlineTeam.objects.get(id=team_id, status='active')
        except OnlineTeam.DoesNotExist:
            return Response({
                'error': 'Online team not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if team.leader == request.user:
            return Response({
                'error': 'Team leader cannot leave the team. You must disband the team instead.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            team_member = TeamMember.objects.get(online_team=team, user=request.user)
            team_member.delete()
            return Response({
                'message': 'Successfully left the online team'
            }, status=status.HTTP_200_OK)
        except TeamMember.DoesNotExist:
            return Response({
                'error': 'You are not a member of this online team'
            }, status=status.HTTP_400_BAD_REQUEST)