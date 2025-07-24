from rest_framework import status, generics
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import F, Sum, Count, Case, When, Value
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .models import Game, GameSession, Leaderboard
from .serializers import (
    SubmitScoreSerializer, LeaderboardSerializer, 
    PlayerRankSerializer, Top10Serializer, GameSessionSerializer
)
from .tasks import update_leaderboard_async

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class SubmitScoreView(generics.CreateAPIView):
    """Submit a game score with atomic transaction and cache invalidation."""
    serializer_class = SubmitScoreSerializer
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        game_id = serializer.validated_data['game_id']
        score = serializer.validated_data['score']
        user_id = serializer.validated_data.get('user_id', 1)  # Default user for demo
        
        try:
            with transaction.atomic():
                # Get or create user and game
                user = User.objects.get(id=user_id)
                game = Game.objects.get(id=game_id)
                
                # Create game session
                session = GameSession.objects.create(
                    user=user,
                    game=game,
                    score=score,
                    is_completed=True,
                    session_end=timezone.now()
                )
                
                # Update or create leaderboard entry
                leaderboard_entry, created = Leaderboard.objects.get_or_create(
                    user=user,
                    game=game,
                    defaults={
                        'total_score': score,
                        'best_score': score,
                        'games_played': 1
                    }
                )
                
                if not created:
                    # Update total score, games played, and best score atomically
                    leaderboard_entry.total_score = F('total_score') + score
                    leaderboard_entry.games_played = F('games_played') + 1
                    leaderboard_entry.best_score = Case(
                        When(best_score__lt=score, then=Value(score)),
                        default=F('best_score')
                    )
                    
                    leaderboard_entry.save(update_fields=[
                        'total_score', 'best_score', 'games_played', 'last_played'
                    ])
                
                # Refresh from database to get updated values
                leaderboard_entry.refresh_from_db()
                
                # Invalidate cache for this game's leaderboard
                cache_key = f"leaderboard_top10_{game_id}"
                cache.delete(cache_key)
                
                # Send WebSocket notification
                self._send_leaderboard_update(game_id, leaderboard_entry)
                
                # Trigger async leaderboard ranking update
                update_leaderboard_async.delay(game_id)
                
                return Response({
                    'message': 'Score submitted successfully',
                    'session_id': session.id,
                    'new_total_score': leaderboard_entry.total_score,
                    'games_played': leaderboard_entry.games_played
                }, status=status.HTTP_201_CREATED)
                
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error submitting score: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _send_leaderboard_update(self, game_id, leaderboard_entry):
        """Send WebSocket update for leaderboard changes."""
        try:
            async_to_sync(channel_layer.group_send)(
                f"leaderboard_{game_id}",
                {
                    'type': 'leaderboard_update',
                    'message': {
                        'user_id': leaderboard_entry.user.id,
                        'username': leaderboard_entry.user.username,
                        'total_score': leaderboard_entry.total_score,
                        'games_played': leaderboard_entry.games_played
                    }
                }
            )
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")


class Top10View(generics.ListAPIView):
    """Get top 10 players for a specific game with caching."""
    serializer_class = Top10Serializer
    
    def get(self, request, game_id):
        # Check cache first
        cache_key = f"leaderboard_top10_{game_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        try:
            # Verify game exists
            game = Game.objects.get(id=game_id, is_active=True)
            
            # Get top 10 with ranking using window function
            from django.db import connection
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
            
            # Cache for 30 seconds
            cache.set(cache_key, results, 30)
            
            return Response(results)
            
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching top 10: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PlayerRankView(generics.RetrieveAPIView):
    """Get a specific player's rank for a game."""
    serializer_class = PlayerRankSerializer
    
    def get(self, request, game_id, user_id):
        try:
            # Verify game and user exist
            game = Game.objects.get(id=game_id, is_active=True)
            user = User.objects.get(id=user_id)
            
            # Get leaderboard entry
            try:
                leaderboard_entry = Leaderboard.objects.get(
                    user_id=user_id, 
                    game_id=game_id
                )
                
                # Calculate rank
                rank = Leaderboard.get_user_rank(user_id, game_id)
                
                response_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'game_id': game.id,
                    'game_name': game.name,
                    'rank': rank,
                    'total_score': leaderboard_entry.total_score,
                    'best_score': leaderboard_entry.best_score,
                    'games_played': leaderboard_entry.games_played,
                    'last_played': leaderboard_entry.last_played
                }
                
                return Response(response_data)
                
            except Leaderboard.DoesNotExist:
                return Response({
                    'user_id': user.id,
                    'username': user.username,
                    'game_id': game.id,
                    'game_name': game.name,
                    'rank': None,
                    'total_score': 0,
                    'best_score': 0,
                    'games_played': 0,
                    'last_played': None
                })
                
        except Game.DoesNotExist:
            return Response(
                {'error': 'Game not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching player rank: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def game_list(request):
    """Get list of all active games."""
    try:
        games = Game.objects.filter(is_active=True).values(
            'id', 'name', 'description', 'created_at'
        )
        return Response(list(games))
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def user_search(request):
    """Search users with pagination."""
    try:
        search_query = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 50:
            page_size = 10
            
        # Build queryset
        queryset = User.objects.filter(is_active=True)
        
        if search_query:
            queryset = queryset.filter(
                username__icontains=search_query
            )
        
        # Order by username for consistent pagination
        queryset = queryset.order_by('username')
        
        # Calculate pagination
        total_count = queryset.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        users = queryset[start_index:end_index].values(
            'id', 'username', 'first_name', 'last_name'
        )
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'users': list(users),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous
            }
        })
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
