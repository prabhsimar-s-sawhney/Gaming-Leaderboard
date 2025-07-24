from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.validators import MinValueValidator


class Game(models.Model):
    """Game model to store different games."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'games'
        ordering = ['name']

    def __str__(self):
        return self.name


class GameSession(models.Model):
    """Game session model to track individual game sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sessions')
    score = models.IntegerField(validators=[MinValueValidator(0)])
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'game_sessions'
        indexes = [
            models.Index(fields=['user'], name='idx_sessions_user'),
            models.Index(fields=['game', 'score'], name='idx_sessions_game_score'),
            models.Index(fields=['session_start'], name='idx_sessions_start'),
        ]
        ordering = ['-session_start']

    def __str__(self):
        return f"{self.user.username} - {self.game.name} - {self.score}"


class Leaderboard(models.Model):
    """Leaderboard model to store aggregated user rankings."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='leaderboard_entries')
    total_score = models.BigIntegerField(default=0)
    best_score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    last_played = models.DateTimeField(auto_now=True)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'leaderboard'
        unique_together = ['user', 'game']
        indexes = [
            models.Index(fields=['game', '-total_score'], name='idx_lb_game_total'),
            models.Index(fields=['game', '-best_score'], name='idx_lb_game_best'),
            models.Index(fields=['rank'], name='idx_lb_rank'),
        ]
        ordering = ['-total_score']

    def __str__(self):
        return f"{self.user.username} - {self.game.name} - {self.total_score}"

    @classmethod
    def get_top_players(cls, game_id, limit=10):
        """Get top players for a specific game."""
        return cls.objects.filter(
            game_id=game_id
        ).select_related(
            'user', 'game'
        ).order_by('-total_score')[:limit]

    @classmethod
    def get_user_rank(cls, user_id, game_id):
        """Get user's rank for a specific game."""
        try:
            entry = cls.objects.get(user_id=user_id, game_id=game_id)
            # Calculate rank using window function
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT rank_position FROM (
                        SELECT id, 
                               RANK() OVER (ORDER BY total_score DESC) as rank_position
                        FROM leaderboard 
                        WHERE game_id = %s
                    ) ranked_table 
                    WHERE id = %s
                """, [game_id, entry.id])
                result = cursor.fetchone()
                return result[0] if result else None
        except cls.DoesNotExist:
            return None
