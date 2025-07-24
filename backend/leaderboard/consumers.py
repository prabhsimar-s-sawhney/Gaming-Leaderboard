import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Game


class LeaderboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time leaderboard updates."""
    
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'leaderboard_{self.game_id}'
        
        # Verify game exists
        game_exists = await self.check_game_exists(self.game_id)
        if not game_exists:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial leaderboard data
        await self.send_initial_leaderboard()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            
            if message_type == 'request_leaderboard':
                await self.send_initial_leaderboard()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def leaderboard_update(self, event):
        """Handle leaderboard update from group."""
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'data': message
        }))
    
    async def send_initial_leaderboard(self):
        """Send current leaderboard state to client."""
        try:
            leaderboard_data = await self.get_leaderboard_data(self.game_id)
            await self.send(text_data=json.dumps({
                'type': 'initial_leaderboard',
                'data': leaderboard_data
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to load leaderboard: {str(e)}'
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
        """Get current leaderboard data for the game."""
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
                    'last_played': row[6].isoformat() if row[6] else None
                })
            
            return results
