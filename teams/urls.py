from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    # Team operations
    path('all/', views.AllTeamsView.as_view(), name='all-teams'),
    
    # In-person team operations
    path('in-person/create/', views.InPersonTeamCreateView.as_view(), name='in-person-team-create'),
    path('in-person/join/', views.InPersonTeamJoinView.as_view(), name='in-person-team-join'),
    path('in-person/<int:team_id>/leave/', views.InPersonTeamLeaveView.as_view(), name='in-person-team-leave'),
    
    # Online team operations
    path('online/create/', views.OnlineTeamCreateView.as_view(), name='online-team-create'),
    path('online/join/', views.OnlineTeamJoinView.as_view(), name='online-team-join'),
    path('online/<int:team_id>/leave/', views.OnlineTeamLeaveView.as_view(), name='online-team-leave'),
    
    # Team details
    path('in-person/<int:pk>/', views.InPersonTeamDetailView.as_view(), name='in-person-team-detail'),
    path('online/<int:pk>/', views.OnlineTeamDetailView.as_view(), name='online-team-detail'),
    
    # Team members
    path('in-person/<int:team_id>/members/', views.InPersonTeamMembersView.as_view(), name='in-person-team-members'),
    path('online/<int:team_id>/members/', views.OnlineTeamMembersView.as_view(), name='online-team-members'),
]
