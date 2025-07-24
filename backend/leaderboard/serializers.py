from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Game, GameSession, Leaderboard


class UserSerializer(serializers.ModelSerializer):
    """User serializer for leaderboard responses."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class GameSerializer(serializers.ModelSerializer):
    """Game serializer."""
    
    class Meta:
        model = Game
        fields = ['id', 'name', 'description', 'created_at', 'is_active']


class GameSessionSerializer(serializers.ModelSerializer):
    """Game session serializer."""
    user = UserSerializer(read_only=True)
    game = GameSerializer(read_only=True)
    
    class Meta:
        model = GameSession
        fields = [
            'id', 'user', 'game', 'score', 'session_start', 
            'session_end', 'is_completed'
        ]


class SubmitScoreSerializer(serializers.Serializer):
    """Serializer for score submission."""
    game_id = serializers.IntegerField()
    score = serializers.IntegerField(min_value=0)
    user_id = serializers.IntegerField(required=False)
    
    def validate_game_id(self, value):
        """Validate game exists and is active."""
        try:
            game = Game.objects.get(id=value, is_active=True)
            return value
        except Game.DoesNotExist:
            raise serializers.ValidationError("Game not found or inactive.")
    
    def validate_score(self, value):
        """Validate score is positive."""
        if value < 0:
            raise serializers.ValidationError("Score must be non-negative.")
        return value


class LeaderboardSerializer(serializers.ModelSerializer):
    """Leaderboard serializer with user details."""
    user = UserSerializer(read_only=True)
    game = GameSerializer(read_only=True)
    rank = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'user', 'game', 'total_score', 'best_score', 
            'games_played', 'last_played', 'rank'
        ]


class PlayerRankSerializer(serializers.Serializer):
    """Serializer for player rank response."""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    game_id = serializers.IntegerField()
    game_name = serializers.CharField()
    rank = serializers.IntegerField(allow_null=True)
    total_score = serializers.IntegerField()
    best_score = serializers.IntegerField()
    games_played = serializers.IntegerField()
    last_played = serializers.DateTimeField()


class Top10Serializer(serializers.Serializer):
    """Serializer for top 10 leaderboard response."""
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    total_score = serializers.IntegerField()
    best_score = serializers.IntegerField()
    games_played = serializers.IntegerField()
    last_played = serializers.DateTimeField()
