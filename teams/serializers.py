from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import InPersonTeam, OnlineTeam, TeamMember

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information in team contexts."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number']


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'is_paid', 'payment_completed_at', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class InPersonTeamSerializer(serializers.ModelSerializer):
    """Serializer for in-person teams."""
    members = TeamMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    leader = UserSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    team_type = serializers.SerializerMethodField()
    
    class Meta:
        model = InPersonTeam
        fields = [
            'id', 'name', 'description', 'team_type', 'status', 'invite_code',
            'leader', 'members', 'member_count', 'created_at', 'updated_at', 
            'is_member', 'can_join', 'payment_status'
        ]
        read_only_fields = ['id', 'invite_code', 'leader', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False
    
    def get_can_join(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_join, _ = obj.can_join(request.user)
            return can_join
        return False
    
    def get_payment_status(self, obj):
        return obj.get_payment_status()
    
    def get_team_type(self, obj):
        return 'in_person'


class OnlineTeamSerializer(serializers.ModelSerializer):
    """Serializer for online teams."""
    members = TeamMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    leader = UserSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    team_type = serializers.SerializerMethodField()
    
    class Meta:
        model = OnlineTeam
        fields = [
            'id', 'name', 'description', 'team_type', 'status', 'invite_code',
            'leader', 'members', 'member_count', 'is_paid', 'payment_completed_at',
            'payment_completed_by', 'created_at', 'updated_at', 'is_member', 
            'can_join', 'payment_status'
        ]
        read_only_fields = ['id', 'invite_code', 'leader', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False
    
    def get_can_join(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_join, _ = obj.can_join(request.user)
            return can_join
        return False
    
    def get_payment_status(self, obj):
        return obj.get_payment_status()
    
    def get_team_type(self, obj):
        return 'online'


class TeamCreateSerializer(serializers.Serializer):
    """Serializer for creating teams."""
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    team_type = serializers.ChoiceField(choices=['in_person', 'online'])
    
    def validate(self, data):
        # Check if user already has a team of this type
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if data['team_type'] == 'in_person':
                existing_team = InPersonTeam.objects.filter(
                    leader=request.user,
                    status='active'
                ).exists()
            else:
                existing_team = OnlineTeam.objects.filter(
                    leader=request.user,
                    status='active'
                ).exists()
            
            if existing_team:
                raise serializers.ValidationError(
                    f"You already have an active {data['team_type']} team"
                )
        return data


class TeamJoinSerializer(serializers.Serializer):
    """Serializer for joining teams with invite code."""
    invite_code = serializers.CharField(max_length=8)
    
    def validate_invite_code(self, value):
        # Try to find team in both types
        team = None
        try:
            team = InPersonTeam.objects.get(invite_code=value, status='active')
        except InPersonTeam.DoesNotExist:
            try:
                team = OnlineTeam.objects.get(invite_code=value, status='active')
            except OnlineTeam.DoesNotExist:
                raise serializers.ValidationError("Invalid invite code")
        
        # Check if user can join this team
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_join, message = team.can_join(request.user)
            if not can_join:
                raise serializers.ValidationError(message)
        
        return value
    
    def save(self, **kwargs):
        invite_code = self.validated_data['invite_code']
        
        # Try to find team in both types
        team = None
        try:
            team = InPersonTeam.objects.get(invite_code=invite_code)
        except InPersonTeam.DoesNotExist:
            team = OnlineTeam.objects.get(invite_code=invite_code)
        
        user = self.context['request'].user
        
        # Create team member
        team_member = TeamMember.objects.create(team=team, user=user)
        return team_member