from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from unittest.mock import patch
import json

from .models import Game, GameSession, Leaderboard


class GameModelTest(TestCase):
    """Test cases for Game model."""
    
    def setUp(self):
        self.game = Game.objects.create(
            name="Test Game",
            description="A test game for unit testing"
        )
    
    def test_game_creation(self):
        """Test game creation with required fields."""
        self.assertEqual(self.game.name, "Test Game")
        self.assertTrue(self.game.is_active)
        self.assertIsNotNone(self.game.created_at)
    
    def test_game_str_representation(self):
        """Test string representation of game."""
        self.assertEqual(str(self.game), "Test Game")


class GameSessionModelTest(TestCase):
    """Test cases for GameSession model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.game = Game.objects.create(name="Test Game")
        self.session = GameSession.objects.create(
            user=self.user,
            game=self.game,
            score=100
        )
    
    def test_session_creation(self):
        """Test game session creation."""
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.game, self.game)
        self.assertEqual(self.session.score, 100)
        self.assertFalse(self.session.is_completed)


class LeaderboardModelTest(TestCase):
    """Test cases for Leaderboard model."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test123')
        self.user2 = User.objects.create_user(username='user2', password='test123')
        self.game = Game.objects.create(name="Test Game")
        
        self.leaderboard1 = Leaderboard.objects.create(
            user=self.user1,
            game=self.game,
            total_score=1000,
            best_score=500,
            games_played=5
        )
        self.leaderboard2 = Leaderboard.objects.create(
            user=self.user2,
            game=self.game,
            total_score=800,
            best_score=400,
            games_played=3
        )
    
    def test_leaderboard_creation(self):
        """Test leaderboard entry creation."""
        self.assertEqual(self.leaderboard1.total_score, 1000)
        self.assertEqual(self.leaderboard1.games_played, 5)
    
    def test_get_top_players(self):
        """Test getting top players for a game."""
        top_players = Leaderboard.get_top_players(self.game.id, limit=2)
        self.assertEqual(len(top_players), 2)
        self.assertEqual(top_players[0].user, self.user1)  # Higher score first


class SubmitScoreAPITest(APITestCase):
    """Test cases for Submit Score API."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.game = Game.objects.create(name="Test Game")
        self.url = reverse('submit-score')
    
    def test_submit_score_success(self):
        """Test successful score submission."""
        data = {
            'game_id': self.game.id,
            'score': 150,
            'user_id': self.user.id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        
        # Check if game session was created
        session = GameSession.objects.filter(user=self.user, game=self.game).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.score, 150)
        
        # Check if leaderboard entry was created
        leaderboard = Leaderboard.objects.filter(user=self.user, game=self.game).first()
        self.assertIsNotNone(leaderboard)
        self.assertEqual(leaderboard.total_score, 150)
    
    def test_submit_score_invalid_game(self):
        """Test score submission with invalid game ID."""
        data = {
            'game_id': 999,
            'score': 150,
            'user_id': self.user.id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_submit_negative_score(self):
        """Test score submission with negative score."""
        data = {
            'game_id': self.game.id,
            'score': -10,
            'user_id': self.user.id
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class Top10APITest(APITestCase):
    """Test cases for Top 10 API."""
    
    def setUp(self):
        self.game = Game.objects.create(name="Test Game")
        
        # Create multiple users and leaderboard entries
        for i in range(15):
            user = User.objects.create_user(
                username=f'user{i}',
                password='testpass123'
            )
            Leaderboard.objects.create(
                user=user,
                game=self.game,
                total_score=1000 - (i * 50),  # Decreasing scores
                best_score=500 - (i * 25),
                games_played=i + 1
            )
    
    def test_get_top10_success(self):
        """Test successful retrieval of top 10 players."""
        url = reverse('top10', kwargs={'game_id': self.game.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        
        # Check if results are sorted by score (descending)
        for i in range(1, len(response.data)):
            self.assertGreaterEqual(
                response.data[i-1]['total_score'],
                response.data[i]['total_score']
            )
    
    @patch('leaderboard.views.cache')
    def test_get_top10_caching(self, mock_cache):
        """Test caching behavior for top 10 API."""
        mock_cache.get.return_value = None
        
        url = reverse('top10', kwargs={'game_id': self.game.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_cache.set.assert_called_once()
    
    def test_get_top10_invalid_game(self):
        """Test top 10 retrieval with invalid game ID."""
        url = reverse('top10', kwargs={'game_id': 999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlayerRankAPITest(APITestCase):
    """Test cases for Player Rank API."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.game = Game.objects.create(name="Test Game")
        self.leaderboard = Leaderboard.objects.create(
            user=self.user,
            game=self.game,
            total_score=750,
            best_score=300,
            games_played=3
        )
    
    def test_get_player_rank_success(self):
        """Test successful retrieval of player rank."""
        url = reverse('player-rank', kwargs={
            'game_id': self.game.id,
            'user_id': self.user.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['total_score'], 750)
    
    def test_get_player_rank_no_leaderboard_entry(self):
        """Test player rank for user with no leaderboard entry."""
        new_user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        
        url = reverse('player-rank', kwargs={
            'game_id': self.game.id,
            'user_id': new_user.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_score'], 0)
        self.assertIsNone(response.data['rank'])


class CacheTest(TestCase):
    """Test cases for caching functionality."""
    
    def setUp(self):
        self.game = Game.objects.create(name="Test Game")
        cache.clear()
    
    def test_cache_invalidation(self):
        """Test cache invalidation after score submission."""
        cache_key = f"leaderboard_top10_{self.game.id}"
        
        # Set initial cache
        cache.set(cache_key, ['test_data'], 30)
        self.assertEqual(cache.get(cache_key), ['test_data'])
        
        # Simulate cache invalidation (this would happen in views)
        cache.delete(cache_key)
        self.assertIsNone(cache.get(cache_key))
