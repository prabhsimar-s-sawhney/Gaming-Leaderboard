from django.urls import path
from . import views

urlpatterns = [
    path('games/', views.game_list, name='game-list'),
    path('users/search/', views.user_search, name='user-search'),
    path('submit-score/', views.SubmitScoreView.as_view(), name='submit-score'),
    path('leaderboard/<int:game_id>/top10/', views.Top10View.as_view(), name='top10'),
    path('leaderboard/<int:game_id>/player/<int:user_id>/', views.PlayerRankView.as_view(), name='player-rank'),
]
