from django.urls import path
from . import views

urlpatterns = [
    # Competition status
    path('status/', views.CompetitionStatusView.as_view(), name='competition-status'),
    
    # Team management
    path('my-team/', views.MyTeamView.as_view(), name='my-team'),
    path('team/create/', views.TeamCreateView.as_view(), name='team-create'),
    path('team/join/', views.TeamJoinView.as_view(), name='team-join'),
    path('team/<int:team_id>/leave/', views.TeamLeaveView.as_view(), name='team-leave'),
    path('team/<int:team_id>/disband/', views.TeamDisbandView.as_view(), name='team-disband'),
    path('team/<int:team_id>/invite-code/', views.TeamInviteCodeRevokeView.as_view(), name='team-invite-revoke'),
    path('team/<int:team_id>/update/', views.TeamUpdateView.as_view(), name='team-update'),
    path('team/<int:team_id>/members/', views.TeamMembersView.as_view(), name='team-members'),
    
    # Submissions
    # path('submission/create/', views.SubmissionCreateView.as_view(), name='submission-create'),
    # path('submissions/', views.SubmissionListView.as_view(), name='submission-list'),
]
