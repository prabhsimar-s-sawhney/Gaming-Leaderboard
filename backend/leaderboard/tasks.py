from celery import shared_task
from django.core.cache import cache
from django.db import connection
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_leaderboard_async(game_id):
    """Asynchronously update leaderboard rankings using window functions."""
    try:
        with connection.cursor() as cursor:
            # Update rankings using MySQL window function
            cursor.execute("""
                UPDATE leaderboard l1
                JOIN (
                    SELECT id, 
                           RANK() OVER (ORDER BY total_score DESC) as new_rank
                    FROM leaderboard 
                    WHERE game_id = %s
                ) l2 ON l1.id = l2.id
                SET l1.rank = l2.new_rank
                WHERE l1.game_id = %s
            """, [game_id, game_id])
            
        # Invalidate related caches
        cache.delete(f"leaderboard_top10_{game_id}")
        
        logger.info(f"Leaderboard rankings updated for game {game_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating leaderboard rankings: {str(e)}")
        return False


@shared_task
def cleanup_old_sessions():
    """Clean up old game sessions (older than 30 days)."""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .models import GameSession
        
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = GameSession.objects.filter(
            session_start__lt=cutoff_date,
            is_completed=True
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old game sessions")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old sessions: {str(e)}")
        return 0


@shared_task
def generate_daily_stats():
    """Generate daily statistics for games and players."""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .models import GameSession, Game
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        stats = {}
        for game in Game.objects.filter(is_active=True):
            daily_sessions = GameSession.objects.filter(
                game=game,
                session_start__date=yesterday,
                is_completed=True
            )
            
            stats[game.name] = {
                'total_games': daily_sessions.count(),
                'unique_players': daily_sessions.values('user').distinct().count(),
                'total_score': sum(session.score for session in daily_sessions)
            }
        
        logger.info(f"Daily stats generated: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating daily stats: {str(e)}")
        return {}


@shared_task
def refresh_leaderboard_cache(game_id):
    """Refresh leaderboard cache for a specific game."""
    try:
        from .models import Leaderboard
        
        # Get fresh top 10 data
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    RANK() OVER (ORDER BY total_score DESC) as `rank`,
                    l.user_id,
                    u.username,
                    l.total_score,
                    l.best_score,
                    l.games_played,
                    l.last_played
                FROM leaderboard l
                JOIN auth_user u ON l.user_id = u.id
                WHERE l.game_id = %s
                ORDER BY l.total_score DESC
                LIMIT 10
            """, [game_id])
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'rank': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'total_score': row[3],
                    'best_score': row[4],
                    'games_played': row[5],
                    'last_played': row[6]
                })
        
        # Update cache
        cache_key = f"leaderboard_top10_{game_id}"
        cache.set(cache_key, results, 30)
        
        logger.info(f"Leaderboard cache refreshed for game {game_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing leaderboard cache: {str(e)}")
        return False
