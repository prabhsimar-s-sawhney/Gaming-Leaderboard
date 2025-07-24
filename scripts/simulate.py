#!/usr/bin/env python3
"""
Gaming Leaderboard Simulation Script

This script simulates game sessions and score submissions to test
the leaderboard system with realistic data.
"""

import os
import sys
import django
import random
import time
import requests
from datetime import datetime, timedelta
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')
django.setup()

from django.contrib.auth.models import User
from leaderboard.models import Game, GameSession, Leaderboard


class LeaderboardSimulator:
    """Simulates gaming activity for leaderboard testing."""
    
    def __init__(self, api_base_url="http://localhost:8000/api"):
        self.api_base_url = api_base_url
        self.games = []
        self.users = []
        
    def create_sample_data(self):
        """Create sample games and users."""
        print("Creating sample data...")
        
        # Create sample games
        game_names = [
            "Space Invaders",
            "Tetris",
            "Pac-Man",
            "Snake",
            "Asteroids"
        ]
        
        for name in game_names:
            game, created = Game.objects.get_or_create(
                name=name,
                defaults={'description': f'Classic {name} game'}
            )
            self.games.append(game)
            if created:
                print(f"Created game: {name}")
        
        # Create sample users
        user_names = [
            "alice", "bob", "charlie", "diana", "eve",
            "frank", "grace", "henry", "iris", "jack",
            "kate", "liam", "mia", "noah", "olivia"
        ]
        
        for username in user_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.capitalize(),
                    'password': 'pbkdf2_sha256$600000$dummy$hash'
                }
            )
            self.users.append(user)
            if created:
                print(f"Created user: {username}")
    
    def simulate_game_sessions(self, num_sessions=100):
        """Simulate random game sessions."""
        print(f"Simulating {num_sessions} game sessions...")
        
        for i in range(num_sessions):
            user = random.choice(self.users)
            game = random.choice(self.games)
            
            # Generate realistic scores based on game type
            if "Tetris" in game.name:
                score = random.randint(500, 10000)
            elif "Space Invaders" in game.name:
                score = random.randint(1000, 25000)
            elif "Pac-Man" in game.name:
                score = random.randint(200, 50000)
            else:
                score = random.randint(100, 15000)
            
            # Submit score via API
            self.submit_score_via_api(game.id, score, user.id)
            
            # Small delay to simulate realistic timing
            time.sleep(0.1)
            
            if (i + 1) % 20 == 0:
                print(f"Completed {i + 1}/{num_sessions} sessions")
    
    def submit_score_via_api(self, game_id, score, user_id):
        """Submit a score via the REST API."""
        try:
            response = requests.post(
                f"{self.api_base_url}/submit-score/",
                json={
                    'game_id': game_id,
                    'score': score,
                    'user_id': user_id
                },
                timeout=10
            )
            
            if response.status_code != 201:
                print(f"API Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            # Fallback to direct database insertion
            self.submit_score_direct(game_id, score, user_id)
    
    def submit_score_direct(self, game_id, score, user_id):
        """Submit score directly to database (fallback)."""
        try:
            user = User.objects.get(id=user_id)
            game = Game.objects.get(id=game_id)
            
            # Create game session
            session = GameSession.objects.create(
                user=user,
                game=game,
                score=score,
                is_completed=True,
                session_end=datetime.now()
            )
            
            # Update leaderboard
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
                leaderboard_entry.total_score += score
                leaderboard_entry.best_score = max(leaderboard_entry.best_score, score)
                leaderboard_entry.games_played += 1
                leaderboard_entry.save()
                
        except Exception as e:
            print(f"Direct submission failed: {e}")
    
    def display_leaderboard_summary(self):
        """Display a summary of the current leaderboard."""
        print("\n" + "="*60)
        print("LEADERBOARD SUMMARY")
        print("="*60)
        
        for game in self.games:
            print(f"\n🎮 {game.name}")
            print("-" * 40)
            
            top_players = Leaderboard.objects.filter(
                game=game
            ).select_related('user').order_by('-total_score')[:5]
            
            if top_players:
                for rank, entry in enumerate(top_players, 1):
                    print(f"{rank:2}. {entry.user.username:12} | "
                          f"Score: {entry.total_score:8,} | "
                          f"Games: {entry.games_played:3}")
            else:
                print("   No players yet")
    
    def test_api_endpoints(self):
        """Test various API endpoints."""
        print("\n" + "="*60)
        print("TESTING API ENDPOINTS")
        print("="*60)
        
        if not self.games or not self.users:
            print("No test data available")
            return
        
        game = self.games[0]
        user = self.users[0]
        
        # Test Top 10 endpoint
        try:
            response = requests.get(
                f"{self.api_base_url}/leaderboard/{game.id}/top10/",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Top 10 API: Retrieved {len(data)} entries")
            else:
                print(f"❌ Top 10 API: {response.status_code}")
        except Exception as e:
            print(f"❌ Top 10 API: {e}")
        
        # Test Player Rank endpoint
        try:
            response = requests.get(
                f"{self.api_base_url}/leaderboard/{game.id}/player/{user.id}/",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Player Rank API: User {data.get('username')} rank {data.get('rank')}")
            else:
                print(f"❌ Player Rank API: {response.status_code}")
        except Exception as e:
            print(f"❌ Player Rank API: {e}")
        
        # Test Games list endpoint
        try:
            response = requests.get(f"{self.api_base_url}/games/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Games API: Retrieved {len(data)} games")
            else:
                print(f"❌ Games API: {response.status_code}")
        except Exception as e:
            print(f"❌ Games API: {e}")
    
    def run_continuous_simulation(self, duration_minutes=5):
        """Run continuous simulation for testing real-time features."""
        print(f"\n🚀 Starting continuous simulation for {duration_minutes} minutes...")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        session_count = 0
        
        while datetime.now() < end_time:
            user = random.choice(self.users)
            game = random.choice(self.games)
            score = random.randint(100, 5000)
            
            self.submit_score_via_api(game.id, score, user.id)
            session_count += 1
            
            # Wait between 1-5 seconds between submissions
            time.sleep(random.uniform(1, 5))
            
            if session_count % 10 == 0:
                remaining = (end_time - datetime.now()).total_seconds()
                print(f"Submitted {session_count} scores, {remaining:.0f}s remaining")
        
        print(f"✅ Continuous simulation completed: {session_count} total submissions")


def main():
    """Main simulation function."""
    print("🎮 Gaming Leaderboard Simulator")
    print("=" * 50)
    
    simulator = LeaderboardSimulator()
    
    # Create sample data
    simulator.create_sample_data()
    
    # Run initial simulation
    simulator.simulate_game_sessions(50)
    
    # Display results
    simulator.display_leaderboard_summary()
    
    # Test API endpoints
    simulator.test_api_endpoints()
    
    # Ask user if they want to run continuous simulation
    print("\n" + "="*60)
    choice = input("Run continuous simulation? (y/N): ").lower().strip()
    
    if choice == 'y':
        try:
            duration = int(input("Duration in minutes (default 2): ") or "2")
            simulator.run_continuous_simulation(duration)
        except KeyboardInterrupt:
            print("\n⚠️  Simulation interrupted by user")
        except ValueError:
            print("Invalid duration, using default of 2 minutes")
            simulator.run_continuous_simulation(2)
    
    print("\n✅ Simulation completed!")


if __name__ == "__main__":
    main()
