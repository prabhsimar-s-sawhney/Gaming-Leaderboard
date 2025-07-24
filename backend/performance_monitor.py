#!/usr/bin/env python
"""
Performance monitoring script for Django Channels WebSocket connections.
Run this script to monitor and diagnose timeout issues.
"""

import os
import sys
import django
import asyncio
import time
from datetime import datetime
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')
django.setup()

from django.core.cache import cache
from django.db import connection
from channels.layers import get_channel_layer
from leaderboard.models import Game, Leaderboard, GameSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance and identify bottlenecks."""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def check_database_performance(self):
        """Check database query performance."""
        logger.info("=== Database Performance Check ===")
        
        start_time = time.time()
        
        # Test basic queries
        try:
            games_count = Game.objects.count()
            sessions_count = GameSession.objects.count()
            leaderboard_count = Leaderboard.objects.count()
            
            query_time = time.time() - start_time
            
            logger.info(f"Games: {games_count}")
            logger.info(f"Sessions: {sessions_count}")
            logger.info(f"Leaderboard entries: {leaderboard_count}")
            logger.info(f"Basic queries took: {query_time:.3f} seconds")
            
            if query_time > 2.0:
                logger.warning("Database queries are slow!")
                
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
    
    def check_cache_performance(self):
        """Check cache performance."""
        logger.info("=== Cache Performance Check ===")
        
        start_time = time.time()
        
        try:
            # Test cache operations
            cache.set('test_key', 'test_value', 30)
            value = cache.get('test_key')
            cache.delete('test_key')
            
            cache_time = time.time() - start_time
            
            logger.info(f"Cache operations took: {cache_time:.3f} seconds")
            
            if cache_time > 0.1:
                logger.warning("Cache operations are slow!")
                
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
    
    async def check_websocket_performance(self):
        """Check WebSocket channel layer performance."""
        logger.info("=== WebSocket Performance Check ===")
        
        if not self.channel_layer:
            logger.error("Channel layer not configured!")
            return
        
        start_time = time.time()
        
        try:
            # Test channel layer operations
            await self.channel_layer.group_add("test_group", "test_channel")
            await self.channel_layer.group_send(
                "test_group",
                {"type": "test.message", "data": "test"}
            )
            await self.channel_layer.group_discard("test_group", "test_channel")
            
            ws_time = time.time() - start_time
            
            logger.info(f"WebSocket operations took: {ws_time:.3f} seconds")
            
            if ws_time > 1.0:
                logger.warning("WebSocket operations are slow!")
                
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
    
    def check_leaderboard_query_performance(self):
        """Check leaderboard-specific query performance."""
        logger.info("=== Leaderboard Query Performance ===")
        
        try:
            games = Game.objects.filter(is_active=True)[:3]
            
            for game in games:
                start_time = time.time()
                
                # Test the actual leaderboard query
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
                        INNER JOIN auth_user u ON l.user_id = u.id
                        WHERE l.game_id = %s
                        ORDER BY l.total_score DESC
                        LIMIT 10
                    """, [game.id])
                    
                    results = cursor.fetchall()
                
                query_time = time.time() - start_time
                
                logger.info(f"Game {game.name} leaderboard query: {query_time:.3f} seconds ({len(results)} results)")
                
                if query_time > 1.0:
                    logger.warning(f"Slow leaderboard query for game {game.name}!")
                    
        except Exception as e:
            logger.error(f"Leaderboard query error: {str(e)}")
    
    def check_system_resources(self):
        """Check system resource usage."""
        logger.info("=== System Resources Check ===")
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"CPU usage: {cpu_percent}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            logger.info(f"Memory usage: {memory.percent}% ({memory.used // (1024**3)} GB used)")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            logger.info(f"Disk usage: {disk.percent}%")
            
            if cpu_percent > 80:
                logger.warning("High CPU usage detected!")
            if memory.percent > 80:
                logger.warning("High memory usage detected!")
            if disk.percent > 80:
                logger.warning("High disk usage detected!")
                
        except ImportError:
            logger.info("psutil not installed, skipping system resource check")
        except Exception as e:
            logger.error(f"System resource check error: {str(e)}")
    
    async def run_full_check(self):
        """Run all performance checks."""
        logger.info(f"Performance check started at {datetime.now()}")
        
        self.check_database_performance()
        self.check_cache_performance()
        await self.check_websocket_performance()
        self.check_leaderboard_query_performance()
        self.check_system_resources()
        
        logger.info("Performance check completed")


async def main():
    """Main function to run performance monitoring."""
    monitor = PerformanceMonitor()
    await monitor.run_full_check()


if __name__ == "__main__":
    asyncio.run(main())
