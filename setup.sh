#!/bin/bash

# Gaming Leaderboard Quick Setup Script
# This script sets up the development environment quickly

set -e

echo "🎮 Gaming Leaderboard Quick Setup"
echo "=================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
# Django Settings
SECRET_KEY=your-development-secret-key-change-this-in-production
DEBUG=True
DJANGO_SETTINGS_MODULE=gaming_leaderboard.settings

# Database Settings
DB_NAME=gaming_leaderboard
DB_USER=root
DB_PASSWORD=rootpassword
DB_HOST=mysql
DB_PORT=3306

# Redis Settings
REDIS_URL=redis://redis:6379/0

# Celery Settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
    echo "✅ Environment file created"
fi

# Start services
echo "🚀 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

# Check if MySQL is ready
echo "🔍 Checking MySQL connection..."
until docker-compose exec -T mysql mysql -u root -prootpassword gaming_leaderboard -e "SELECT 1;" &> /dev/null; do
    echo "   Waiting for MySQL..."
    sleep 3
done
echo "✅ MySQL is ready"

# Check if Redis is ready
echo "🔍 Checking Redis connection..."
until docker-compose exec -T redis redis-cli ping | grep -q PONG; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T backend python manage.py migrate

# Create superuser (optional)
echo "👤 Creating superuser (optional)..."
echo "Do you want to create a Django superuser? (y/N)"
read -r create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Create sample data
echo "📊 Creating sample games..."
docker-compose exec -T backend python manage.py shell << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')
django.setup()

from leaderboard.models import Game
from django.contrib.auth.models import User

try:
    # Create sample games
    games_data = [
        {"name": "Space Invaders", "description": "Classic arcade space shooter game"},
        {"name": "Tetris", "description": "Block-stacking puzzle game"},
        {"name": "Pac-Man", "description": "Classic maze chase game"},
        {"name": "Snake", "description": "Classic snake growing game"},
        {"name": "Asteroids", "description": "Space shooting game with asteroids"},
    ]

    for game_data in games_data:
        game, created = Game.objects.get_or_create(
            name=game_data["name"],
            defaults={"description": game_data["description"]}
        )
        if created:
            print(f"Created game: {game.name}")
        else:
            print(f"Game already exists: {game.name}")

    # Create sample users
    users_data = [
        {"username": "alice", "email": "alice@example.com", "first_name": "Alice"},
        {"username": "bob", "email": "bob@example.com", "first_name": "Bob"},
        {"username": "charlie", "email": "charlie@example.com", "first_name": "Charlie"},
        {"username": "diana", "email": "diana@example.com", "first_name": "Diana"},
        {"username": "eve", "email": "eve@example.com", "first_name": "Eve"},
    ]

    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "password": "pbkdf2_sha256$600000$dummy$hash"
            }
        )
        if created:
            print(f"Created user: {user.username}")
        else:
            print(f"User already exists: {user.username}")

    print("Sample data creation completed!")
    
except Exception as e:
    print(f"Error creating sample data: {e}")
    
EOF

# Test the setup
echo "🧪 Testing the setup..."
sleep 5

# Test backend
if curl -f -s http://localhost:8000/api/games/ > /dev/null; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding"
fi

# Test frontend
if curl -f -s http://localhost:3000/ > /dev/null; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend is not responding"
fi

# Show status
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📱 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000/api/"
echo "   Admin:     http://localhost:8000/admin/"
echo ""
echo "🛠️  Development commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"
echo "   Shell access:  docker-compose exec backend python manage.py shell"
echo "   MySQL access:  docker-compose exec mysql mysql -u root -prootpassword gaming_leaderboard"
echo "   Redis CLI:     docker-compose exec redis redis-cli"
echo ""
echo "🎮 Background Task Commands:"
echo "   View Celery logs: docker-compose logs -f celery"
echo "   Check Celery beat: docker-compose logs -f celery-beat"
echo ""
echo "🧪 Test the simulation:"
echo "   python scripts/simulate.py"
echo ""
echo "Happy coding! 🚀"
