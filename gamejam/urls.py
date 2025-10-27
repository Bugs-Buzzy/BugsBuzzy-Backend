from django.urls import path, include
from .views import MyTeamView, TeamCreateView, TeamJoinView, TeamLeaveView, TeamUpdateView, TeamDeleteView, TeamActivateView, CompetitionStatusView, SubmissionCreateView, SubmissionListView

app_name = "gamejam"

urlpatterns = [
    path("my-team/", MyTeamView.as_view(), name="my_team"),
    path("create/", TeamCreateView.as_view(), name="create"),
    path("join/", TeamJoinView.as_view(), name="join"),
    path("<int:team_id>/leave/", TeamLeaveView.as_view(), name="leave"),
    path("<int:team_id>/update/", TeamUpdateView.as_view(), name="update"),
    path("<int:team_id>/delete/", TeamDeleteView.as_view(), name="delete"),
    path("<int:team_id>/activate/", TeamActivateView.as_view(), name="activate"),
    path("competition/", include([
        path("status/", CompetitionStatusView.as_view(), name="competition_status"),
        path("submission/", SubmissionCreateView.as_view(), name="submission_create"),
        path("submissions/", SubmissionListView.as_view(), name="submission_list"),
    ])),
]
