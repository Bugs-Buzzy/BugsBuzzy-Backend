from django.urls import path, include
from . import views

app_name = "gamejam"

urlpatterns = [
    path("my-team/", views.MyTeamView.as_view(), name="my_team"),
    path("create/", views.TeamCreateView.as_view(), name="create"),
    path("join/", views.TeamJoinView.as_view(), name="join"),
    path("<int:team_id>/leave/", views.TeamLeaveView.as_view(), name="leave"),
    path("<int:team_id>/update/", views.TeamUpdateView.as_view(), name="update"),
    path("<int:team_id>/delete/", views.TeamDeleteView.as_view(), name="delete"),
    path("<int:team_id>/activate/", views.TeamActivateView.as_view(), name="activate"),
    path("verify-team-code/", views.VerifyTeamCodeView.as_view(), name="verify_team_code"),
    path(
        "competition/",
        include(
            [
                path("status/", CompetitionStatusView.as_view(), name="competition_status"),
                path("submission/", SubmissionCreateView.as_view(), name="submission_create"),
                path("submissions/", SubmissionListView.as_view(), name="submission_list"),
            ]
        ),
    ),
]
