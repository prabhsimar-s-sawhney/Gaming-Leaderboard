import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Game


class LeaderboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time leaderboard updates."""
    
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'leaderboard_{self.game_id}'
        
        try:
            # Verify game exists with timeout
            game_exists = await asyncio.wait_for(
                self.check_game_exists(self.game_id), 
                timeout=5.0
            )
            if not game_exists:
                await self.close(code=4004)  # Not found
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send initial leaderboard data in background
            asyncio.create_task(self.send_initial_leaderboard())
            
        except asyncio.TimeoutError:
            await self.close(code=4008)  # Request timeout
        except Exception as e:
            await self.close(code=4500)  # Internal error
    
    async def disconnect(self, close_code):
        # Leave room group with timeout protection
        try:
            await asyncio.wait_for(
                self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                ),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            pass  # Don't block disconnect on timeout
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages with timeout protection."""
        try:
            # Parse JSON with size limit
            if len(text_data) > 1024:  # 1KB limit
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Message too large'
                }))
                return
                
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'request_leaderboard':
                # Handle in background to avoid blocking
                asyncio.create_task(self.send_initial_leaderboard())
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Processing error'
            }))
    
    async def leaderboard_update(self, event):
        """Handle leaderboard update from group."""
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'data': message
        }))
    
    async def send_initial_leaderboard(self):
        """Send current leaderboard state to client with timeout protection."""
        try:
            leaderboard_data = await asyncio.wait_for(
                self.get_leaderboard_data(self.game_id),
                timeout=10.0
            )
            await self.send(text_data=json.dumps({
                'type': 'initial_leaderboard',
                'data': leaderboard_data
            }))
        except asyncio.TimeoutError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Leaderboard request timed out'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to load leaderboard'
            }))
    
    @database_sync_to_async
    def check_game_exists(self, game_id):
        """Check if game exists and is active."""
        try:
            return Game.objects.filter(id=game_id, is_active=True).exists()
        except:
            return False
    
    @database_sync_to_async
    def get_leaderboard_data(self, game_id):
        """Get current leaderboard data for the game with optimized query."""
        from django.db import connection
        from django.core.cache import cache
        
        # Try cache first
        cache_key = f"ws_leaderboard_{game_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            with connection.cursor() as cursor:
                # Optimized query with connection timeout
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
                    INNER JOIN auth_user u ON l.user_id = u.id
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
                        'last_played': row[6].isoformat() if row[6] else None
                    })
                
                # Cache for 15 seconds to reduce database load
                cache.set(cache_key, results, 15)
                return results
                
        except Exception as e:
            # Return empty result on error to prevent crashes
            return []
