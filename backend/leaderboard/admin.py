from django.contrib import admin
from .models import Game, GameSession, Leaderboard


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'score', 'session_start', 'is_completed']
    list_filter = ['game', 'is_completed', 'session_start']
    search_fields = ['user__username', 'game__name']
    readonly_fields = ['session_start']
    raw_id_fields = ['user', 'game']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'total_score', 'best_score', 'games_played', 'rank']
    list_filter = ['game', 'last_played']
    search_fields = ['user__username', 'game__name']
    readonly_fields = ['last_played']
    raw_id_fields = ['user', 'game']
    ordering = ['-total_score']
