#!/usr/bin/env python
"""
Optimized data population script for Gaming Leade    # ─── Create Users ──────────────────────────────────────────────────────────────
    print(f"Creating {args.users} users…")

    # Pre-generate all usernames for better performanced.

This script creates fake users, games, and game sessions for testing purposes.
Optimized for performance with bulk operations and database transactions.
"""
import os
import django
import random
import time
from datetime import datetime, timedelta
from faker import Faker
import argparse

# ─── Configure Django ─────────────────────────────────────────────────────────
# Change 'gaming_leaderboard.settings' to wherever your settings.py lives
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from leaderboard.models import Game, GameSession, Leaderboard  # adjust import if your app name differs
from django.db.models import Sum, Count, Max
from django.db import transaction
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

# Start timing
start_time = time.time()

User = get_user_model()

print("🚀 Starting optimized data population................")
print("="*50)

# Wrap the entire operation in a transaction for better performance
with transaction.atomic():
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

    # Get existing usernames from the database to avoid duplicates
    print("  Checking existing usernames...")
    existing_usernames = set(User.objects.values_list('username', flat=True))
    print(f"  Found {len(existing_usernames)} existing users in database")

    # Pre-generate all usernames for better performance
    print("  Generating unique usernames...")
    usernames = []
    base_names = [fake.user_name() for _ in range(args.users * 3)]  # Generate more than needed
    used_names = existing_usernames.copy()  # Include existing usernames in our check

    for i, base_name in enumerate(base_names):
        if len(usernames) >= args.users:
            break
        
        # Clean username and make it unique
        clean_name = base_name.replace('.', '_').replace('-', '_')
        if clean_name not in used_names:
            usernames.append(clean_name)
            used_names.add(clean_name)
        else:
            # Add suffix if duplicate
            counter = 1
            while True:
                unique_name = f"{clean_name}_{counter}"
                if unique_name not in used_names:
                    usernames.append(unique_name)
                    used_names.add(unique_name)
                    break
                counter += 1

    # Ensure we have enough usernames
    counter = 1
    while len(usernames) < args.users:
        username = f"user_{counter}"
        if username not in used_names:
            usernames.append(username)
            used_names.add(username)
        counter += 1

    print(f"  Generated {len(usernames)} unique usernames")

    # Create user objects in bulk with pre-hashed password
    print("  Preparing user objects...")
    hashed_password = make_password("password123")  # Hash once, reuse for all users
    user_objects = []
    for username in usernames:
        user_objects.append(User(
            username=username,
            password=hashed_password  # Reuse the same hashed password
        ))

    # Bulk create users - much faster!
    try:
        User.objects.bulk_create(user_objects, batch_size=1000, ignore_conflicts=True)
        print(f"  Bulk created {len(user_objects)} users")
    except django.db.utils.IntegrityError as e:
        print(f"  Error during bulk creation: {e}")
        print("  Falling back to individual user creation...")
        created_count = 0
        for user_obj in user_objects:
            try:
                user_obj.save()
                created_count += 1
            except django.db.utils.IntegrityError:
                print(f"    Skipped duplicate username: {user_obj.username}")
        print(f"  Created {created_count} users individually")

    # Get user IDs efficiently without loading full user objects
    print("  Getting user IDs for session creation...")
    user_count = User.objects.count()
    print(f"  Found {user_count} total users in database")
    
    # Get user IDs only (much more memory efficient)
    user_ids = list(User.objects.values_list('id', flat=True))
    print(f"  Retrieved {len(user_ids)} user IDs")

    # ─── Create Game Sessions ────────────────────────────────────────────────────
    print(f"Creating {args.sessions} game sessions…")

    # Pre-calculate random data for bulk creation
    past = datetime.now() - timedelta(days=30)

    # Pre-calculate user and game choices for better performance
    game_ids = [game.id for game in games]

    print("  Generating session data...")
    
    # Process sessions in smaller batches to avoid memory issues
    batch_size = 2000
    total_created = 0
    
    for batch_start in range(0, args.sessions, batch_size):
        batch_end = min(batch_start + batch_size, args.sessions)
        batch_sessions = batch_end - batch_start
        
        print(f"  Processing batch {batch_start + 1}-{batch_end} ({batch_sessions} sessions)...")
        
        # Generate batch data
        batch_user_ids = [random.choice(user_ids) for _ in range(batch_sessions)]
        batch_game_ids = [random.choice(game_ids) for _ in range(batch_sessions)]
        batch_scores = [random.randint(0, 5000) for _ in range(batch_sessions)]
        batch_timestamps = [fake.date_time_between(start_date=past, end_date="now") for _ in range(batch_sessions)]
        
        # Create session objects for this batch
        batch_objects = []
        for i in range(batch_sessions):
            batch_objects.append(GameSession(
                user_id=batch_user_ids[i],
                game_id=batch_game_ids[i],
                score=batch_scores[i],
                session_start=batch_timestamps[i],
                is_completed=True
            ))
        
        # Bulk insert this batch
        GameSession.objects.bulk_create(batch_objects, batch_size=1000)
        total_created += len(batch_objects)
        
        # Clear memory
        del batch_objects, batch_user_ids, batch_game_ids, batch_scores, batch_timestamps
        
        print(f"    Created {batch_sessions} sessions (Total: {total_created})")
    
    print(f"  ✅ Bulk created {total_created} game sessions")

    # ─── Backfill Leaderboard ────────────────────────────────────────────────────
    # If you have a persisted Leaderboard model, update it now.
    print("Backfilling Leaderboard totals…")

    # Clear existing leaderboard entries for a fresh start
    print("  Clearing existing leaderboard entries...")
    Leaderboard.objects.all().delete()

    # Use a single optimized query to get all leaderboard data
    print("  Calculating leaderboard stats...")
    leaderboard_data = GameSession.objects.values("user_id", "game_id").annotate(
        total_score=Sum("score"),
        games_played=Count("id"),
        best_score=Max("score")
    ).filter(total_score__gt=0)  # Only include users who have played

    # Create leaderboard objects in bulk
    print("  Preparing leaderboard entries...")
    leaderboard_objects = []
    for data in leaderboard_data:
        leaderboard_objects.append(Leaderboard(
            user_id=data["user_id"],
            game_id=data["game_id"],
            total_score=data["total_score"],
            games_played=data["games_played"],
            best_score=data["best_score"]
        ))

    # Bulk create all leaderboard entries at once
    if leaderboard_objects:
        print(f"  Bulk creating {len(leaderboard_objects)} leaderboard entries...")
        Leaderboard.objects.bulk_create(leaderboard_objects, batch_size=2000)
        print(f"  ✅ Created {len(leaderboard_objects)} leaderboard entries")

# Transaction completed
print("Done! 🎮")

# End timing
end_time = time.time()
total_time = end_time - start_time

# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("📊 DATA POPULATION SUMMARY")
print("="*50)
print(f"✅ Games created/found: {len(games)}")
print(f"✅ Total users in database: {user_count}")
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
print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
print(f"📈 Performance: {args.sessions/total_time:.0f} sessions/second")
