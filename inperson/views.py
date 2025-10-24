from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from accounts.permissions import HasPurchased
from .models import InPersonTeam, InPersonMember, InPersonCompetition
from .serializers import (
    InPersonTeamSerializer, 
    InPersonMemberSerializer, 
    InPersonCompetitionSerializer
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
        team = InPersonTeam.objects.filter(leader=request.user).exclude(status='disbanded').first()
        
        # Check if user is member
        if not team:
            membership = InPersonMember.objects.filter(user=request.user).exclude(team__status='disbanded').select_related('team').first()
            if membership:
                team = membership.team
        
        if team:
            serializer = InPersonTeamSerializer(team, context={'request': request})
            return Response({'team': serializer.data})
        
        return Response({'team': None})


class TeamCreateView(APIView):
    """Create a new team"""
    permission_classes = [permissions.IsAuthenticated, HasPurchased('inperson')]
    
    def post(self, request):
        # Check if already has team (any non-disbanded)
        if InPersonTeam.objects.filter(leader=request.user).exclude(status='disbanded').exists():
            return Response({'error': 'You already have an active team'}, status=status.HTTP_400_BAD_REQUEST)
        
        if InPersonMember.objects.filter(user=request.user).exclude(team__status='disbanded').exists():
            return Response({'error': 'You are already a member of another team'}, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name')
        description = request.data.get('description', '')
        avatar = request.data.get('avatar', '')
        
        if not name:
            return Response({'error': 'Team name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            team = InPersonTeam.objects.create(
                name=name,
                description=description,
                avatar=avatar,
                leader=request.user
            )
            serializer = InPersonTeamSerializer(team, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamJoinView(APIView):
    """Join a team with invite code"""
    permission_classes = [permissions.IsAuthenticated, HasPurchased('inperson')]
    
    def post(self, request):
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({'error': 'Invite code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            team = InPersonTeam.objects.exclude(status='disbanded').get(invite_code=invite_code)
        except InPersonTeam.DoesNotExist:
            return Response({'error': 'Invalid invite code'}, status=status.HTTP_404_NOT_FOUND)
        
        can_join, message = team.can_join(request.user)
        if not can_join:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            InPersonMember.objects.create(user=request.user, team=team)
            serializer = InPersonTeamSerializer(team, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamLeaveView(APIView):
    """Leave team"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id)
        
        if team.leader == request.user:
            return Response({'error': 'Team leader cannot leave. Disband team instead.'}, status=status.HTTP_400_BAD_REQUEST)
        
        membership = InPersonMember.objects.filter(user=request.user, team=team).first()
        if not membership:
            return Response({'error': 'You are not a member of this team'}, status=status.HTTP_404_NOT_FOUND)
        
        membership.delete()
        return Response({'message': 'Left team successfully'})


class TeamDisbandView(APIView):
    """Disband team (leader only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)
        team.disband()
        return Response({'message': 'Team disbanded successfully'})


class TeamInviteCodeRevokeView(APIView):
    """Revoke and regenerate invite code (leader only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)
        team.revoke_invite_code()
        serializer = InPersonTeamSerializer(team, context={'request': request})
        return Response({
            'message': 'Invite code revoked and regenerated',
            'new_invite_code': team.invite_code,
            'team': serializer.data
        })


class TeamUpdateView(APIView):
    """Update team info (leader only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, team_id):
        team = get_object_or_404(InPersonTeam, id=team_id, leader=request.user)
        
        if 'name' in request.data:
            team.name = request.data['name']
        if 'description' in request.data:
            team.description = request.data['description']
        if 'avatar' in request.data:
            team.avatar = request.data['avatar']
        
        team.save()
        serializer = InPersonTeamSerializer(team, context={'request': request})
        return Response(serializer.data)


class TeamMembersView(APIView):
    """Get team members"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, team_id):
        team = get_object_or_404(InPersonTeam.objects.exclude(status='disbanded'), id=team_id)
        
        if not team.is_member(request.user):
            return Response({'error': 'You are not a member of this team'}, status=status.HTTP_403_FORBIDDEN)
        
        members = InPersonMember.objects.filter(team=team).select_related('user')
        serializer = InPersonMemberSerializer(members, many=True)
        return Response(serializer.data)


# class SubmissionCreateView(APIView):
#     """Submit for a phase"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         # Get user's team
#         team = InPersonTeam.objects.filter(leader=request.user, status='active').first()
#         if not team:
#             membership = InPersonMember.objects.filter(user=request.user, team__status='active').select_related('team').first()
#             if membership:
#                 team = membership.team
        
#         if not team:
#             return Response({'error': 'You are not in a team'}, status=status.HTTP_400_BAD_REQUEST)
        
#         phase = request.data.get('phase')
#         comp = InPersonCompetition.get_solo()
        
#         # Check if phase is active
#         phase_active = getattr(comp, f'phase_{phase}_active', False)
#         if not phase_active:
#             return Response({'error': f'Phase {phase} is not active yet'}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Create or update submission
#         submission, created = InPersonSubmission.objects.update_or_create(
#             team=team,
#             phase=phase,
#             defaults={
#                 'title': request.data.get('title', ''),
#                 'description': request.data.get('description', ''),
#                 'game_url': request.data.get('game_url', ''),
#             }
#         )
        
#         serializer = InPersonSubmissionSerializer(submission)
#         return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# class SubmissionListView(APIView):
#     """Get team's submissions"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         # Get user's team (any non-disbanded)
#         team = InPersonTeam.objects.filter(leader=request.user).exclude(status='disbanded').first()
#         if not team:
#             membership = InPersonMember.objects.filter(user=request.user).exclude(team__status='disbanded').select_related('team').first()
#             if membership:
#                 team = membership.team
        
#         if not team:
#             return Response({'submissions': []})
        
#         submissions = InPersonSubmission.objects.filter(team=team)
#         serializer = InPersonSubmissionSerializer(submissions, many=True)
#         return Response({'submissions': serializer.data})
