from django.urls import path
from .views import MyAnnouncementsView

urlpatterns = [
    path("my/", MyAnnouncementsView.as_view(), name="my_announcements"),
]
