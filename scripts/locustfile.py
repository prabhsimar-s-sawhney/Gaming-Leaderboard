"""
Locust performance test file for Gaming Leaderboard
"""

from locust import HttpUser, task, between
import random
import json


class GameLeaderboardUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts."""
        # Get available games
        response = self.client.get("/api/games/")
        if response.status_code == 200:
            self.games = response.json()
        else:
            self.games = [{"id": 1, "name": "Test Game"}]
    
    @task(3)
    def view_leaderboard(self):
        """View leaderboard - most common action."""
        game_id = random.choice(self.games)["id"]
        self.client.get(f"/api/leaderboard/{game_id}/top10/")
    
    @task(2)
    def view_player_rank(self):
        """View player rank."""
        game_id = random.choice(self.games)["id"]
        user_id = random.randint(1, 15)
        self.client.get(f"/api/leaderboard/{game_id}/player/{user_id}/")
    
    @task(1)
    def submit_score(self):
        """Submit a score - less frequent but important."""
        game_id = random.choice(self.games)["id"]
        user_id = random.randint(1, 15)
        score = random.randint(100, 10000)
        
        data = {
            "game_id": game_id,
            "score": score,
            "user_id": user_id
        }
        
        self.client.post("/api/submit-score/", json=data)
    
    @task(1)
    def view_games(self):
        """View available games."""
        self.client.get("/api/games/")


class WebSocketUser(HttpUser):
    """Test WebSocket connections (simulated via HTTP for now)."""
    wait_time = between(2, 5)
    
    @task
    def simulate_websocket_connection(self):
        """Simulate WebSocket behavior with HTTP polling."""
        game_id = 1
        # Simulate initial connection by getting leaderboard
        self.client.get(f"/api/leaderboard/{game_id}/top10/")
        
        # Simulate periodic updates
        for _ in range(3):
            self.wait()
            self.client.get(f"/api/leaderboard/{game_id}/top10/")


class HighLoadUser(HttpUser):
    """Simulate high-load scenarios."""
    wait_time = between(0.5, 1)
    
    def on_start(self):
        response = self.client.get("/api/games/")
        if response.status_code == 200:
            self.games = response.json()
        else:
            self.games = [{"id": 1}]
    
    @task(5)
    def rapid_leaderboard_requests(self):
        """Rapid consecutive leaderboard requests."""
        game_id = random.choice(self.games)["id"]
        self.client.get(f"/api/leaderboard/{game_id}/top10/")
    
    @task(2)
    def burst_score_submissions(self):
        """Burst of score submissions."""
        game_id = random.choice(self.games)["id"]
        user_id = random.randint(1, 100)  # More users for high load
        score = random.randint(100, 50000)
        
        data = {
            "game_id": game_id,
            "score": score,
            "user_id": user_id
        }
        
        self.client.post("/api/submit-score/", json=data)
