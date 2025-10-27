from django.urls import path
from . import views

urlpatterns = [
    path("status/", views.MinigameStatusView.as_view(), name="minigame_status"),
    path("submit/", views.MinigameSubmitView.as_view(), name="minigame_submit"),
]
