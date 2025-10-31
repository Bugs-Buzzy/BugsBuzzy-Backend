from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_leaderboard, name='leaderboard-public'),
    path('ranked/', views.ranked_leaderboard, name='leaderboard-ranked'),
]
