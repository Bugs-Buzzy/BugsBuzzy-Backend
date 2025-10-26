from django.urls import path
from .views import MyTeamView, TeamCreateView, TeamJoinView, TeamLeaveView

app_name = "gamejam"

urlpatterns = [
    path("my-team/", MyTeamView.as_view(), name="my_team"),
    path("create/", TeamCreateView.as_view(), name="create"),
    path("join/", TeamJoinView.as_view(), name="join"),
    path("<int:team_id>/leave/", TeamLeaveView.as_view(), name="leave"),
]
