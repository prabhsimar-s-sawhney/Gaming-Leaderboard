#!/usr/bin/env python
import os
import django
import random
from datetime import datetime, timedelta
from faker import Faker
import argparse

# ─── Configure Django ─────────────────────────────────────────────────────────
# Change 'gaming_leaderboard.settings' to wherever your settings.py lives
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')
django.setup()

from django.contrib.auth import get_user_model
from leaderboard.models import Game, GameSession, Leaderboard  # adjust import if your app name differs
from django.db.models import Sum, Count, Max
import django.db.utils

# ─── Faker + CLI setup ────────────────────────────────────────────────────────
fake = Faker()

parser = argparse.ArgumentParser(
    description="Seed the DB with fake users and game sessions."
)
parser.add_argument(
    "--users", "-u", type=int, default=50,
    help="Number of users to create"
)
parser.add_argument(
    "--sessions", "-s", type=int, default=1000,
    help="Number of game sessions to create"
)
parser.add_argument(
    "--games", "-g", type=int, default=5,
    help="Number of games to create"
)
args = parser.parse_args()

User = get_user_model()

# ─── Create Games ──────────────────────────────────────────────────────────────
print(f"Creating {args.games} games…")
game_names = [
    "Space Invaders", "Tetris", "Pac-Man", "Snake", "Asteroids",
    "Breakout", "Frogger", "Centipede", "Galaga", "Donkey Kong"
]
games = []
for i in range(args.games):
    name = game_names[i] if i < len(game_names) else f"Game {i+1}"
    game, created = Game.objects.get_or_create(
        name=name,
        defaults={"description": f"Classic arcade game: {name}"}
    )
    games.append(game)
    if created:
        print(f"  Created: {game.name}")
    else:
        print(f"  Exists: {game.name}")

# ─── Create Users ──────────────────────────────────────────────────────────────
print(f"Creating {args.users} users…")
users = []
for i in range(args.users):
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Generate a unique username by combining fake username with attempt number if needed
            base_username = fake.user_name()
            username = base_username if attempt == 0 else f"{base_username}_{attempt}"
            
            # Try to create user
            u = User.objects.create_user(username=username, password="password123")
            users.append(u)
            print(f"  Created user: {username}")
            break
        except django.db.utils.IntegrityError:
            # Username already exists, try again
            if attempt == max_attempts - 1:
                print(f"  Failed to create unique username after {max_attempts} attempts")
                # Create a guaranteed unique username
                username = f"user_{i}_{random.randint(1000, 9999)}"
                u = User.objects.create_user(username=username, password="password123")
                users.append(u)
                print(f"  Created user with fallback name: {username}")
            continue

# ─── Create Game Sessions ────────────────────────────────────────────────────
print(f"Creating {args.sessions} game sessions…")
for _ in range(args.sessions):
    user = random.choice(users)
    game = random.choice(games)
    score = random.randint(0, 5000)
    # random timestamp in the past 30 days
    past = datetime.now() - timedelta(days=30)
    session_start = fake.date_time_between(start_date=past, end_date="now")
    
    GameSession.objects.create(
        user=user,
        game=game,
        score=score,
        session_start=session_start,
        is_completed=True
    )

# ─── Backfill Leaderboard ────────────────────────────────────────────────────
# If you have a persisted Leaderboard model, update it now.
print("Backfilling Leaderboard totals…")
for game in games:
    print(f"  Processing game: {game.name}")
    # Get aggregated stats per user for this game
    qs = GameSession.objects.filter(game=game).values("user").annotate(
        total=Sum("score"),
        count=Count("id"),
        best=Max("score")
    )
    
    for row in qs:
        user_id = row["user"]
        total_score = row["total"] or 0
        games_played = row["count"] or 0
        best_score = row["best"] or 0
        
        Leaderboard.objects.update_or_create(
            user_id=user_id,
            game=game,
            defaults={
                "total_score": total_score,
                "games_played": games_played,
                "best_score": best_score
            }
        )

print("Done! 🎮")

# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("📊 DATA POPULATION SUMMARY")
print("="*50)
print(f"✅ Games created/found: {len(games)}")
print(f"✅ Users created: {len(users)}")
print(f"✅ Game sessions created: {args.sessions}")

total_leaderboard_entries = Leaderboard.objects.count()
print(f"✅ Leaderboard entries: {total_leaderboard_entries}")

print("\n🎮 Sample leaderboard (top 5 players):")
for game in games[:3]:  # Show top players for first 3 games
    print(f"\n🏆 {game.name}:")
    top_players = Leaderboard.objects.filter(game=game).order_by('-total_score')[:5]
    for i, entry in enumerate(top_players, 1):
        print(f"  {i}. {entry.user.username}: {entry.total_score} points ({entry.games_played} games)")

print(f"\n🚀 You can now test your leaderboard with {args.sessions} game sessions!")
print("Run the Django server and check the API endpoints.")
