# Gaming Leaderboard - Low Level Design (LLD)

## Database Schema Design

### Entity Relationship Diagram
```sql
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     User        │     │   GameSession   │     │   Leaderboard   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────┤ user_id (FK)    │     │ user_id (FK)    │◄─┐
│ username        │     │ game_id (FK)    │────►│ game_id (FK)    │  │
│ email           │     │ score           │     │ total_score     │  │
│ first_name      │     │ session_start   │     │ best_score      │  │
│ last_name       │     │ session_end     │     │ games_played    │  │
│ date_joined     │     │ is_completed    │     │ last_played     │  │
└─────────────────┘     └─────────────────┘     │ rank            │  │
                                │               └─────────────────┘  │
                                │                                    │
                        ┌─────────────────┐                          │
                        │      Game       │                          │
                        ├─────────────────┤                          │
                        │ id (PK)         │◄─────────────────────────┘
                        │ name            │
                        │ description     │
                        │ created_at      │
                        │ is_active       │
                        └─────────────────┘
```

### Table Definitions

#### Games Table
```sql
CREATE TABLE games (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    INDEX idx_games_active (is_active),
    INDEX idx_games_created (created_at)
);
```

#### Game Sessions Table
```sql
CREATE TABLE game_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    session_start DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_end DATETIME NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    
    INDEX idx_game_sessions_user (user_id),
    INDEX idx_game_sessions_game_score (game_id, score),
    INDEX idx_game_sessions_start (session_start),
    INDEX idx_game_sessions_completed (is_completed)
);
```

#### Leaderboard Table
```sql
CREATE TABLE leaderboard (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    game_id BIGINT NOT NULL,
    total_score BIGINT NOT NULL DEFAULT 0,
    best_score INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0,
    last_played DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    rank INTEGER NULL,
    
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_user_game (user_id, game_id),
    INDEX idx_leaderboard_game_total_score (game_id, total_score DESC),
    INDEX idx_leaderboard_game_best_score (game_id, best_score DESC),
    INDEX idx_leaderboard_rank (rank)
);
```

## API Design Specifications

### Score Submission Endpoint

#### Request
```http
POST /api/submit-score/
Content-Type: application/json

{
    "game_id": 1,
    "score": 1500,
    "user_id": 42
}
```

#### Response
```json
{
    "message": "Score submitted successfully",
    "session_id": 12345,
    "new_total_score": 15750,
    "games_played": 12
}
```

#### Implementation Flow
```python
@transaction.atomic
def submit_score(game_id, score, user_id):
    # 1. Validate inputs
    user = User.objects.get(id=user_id)
    game = Game.objects.get(id=game_id, is_active=True)
    
    # 2. Create game session
    session = GameSession.objects.create(
        user=user,
        game=game,
        score=score,
        is_completed=True,
        session_end=timezone.now()
    )
    
    # 3. Update leaderboard atomically
    leaderboard, created = Leaderboard.objects.get_or_create(
        user=user, game=game,
        defaults={
            'total_score': score,
            'best_score': score,
            'games_played': 1
        }
    )
    
    if not created:
        leaderboard.total_score = F('total_score') + score
        leaderboard.best_score = Max('best_score', score)
        leaderboard.games_played = F('games_played') + 1
        leaderboard.save()
    
    # 4. Invalidate cache
    cache.delete(f"leaderboard_top10_{game_id}")
    
    # 5. Send WebSocket update
    channel_layer.group_send(...)
    
    # 6. Queue ranking update
    update_leaderboard_async.delay(game_id)
```

### Top 10 Leaderboard Endpoint

#### Request
```http
GET /api/leaderboard/1/top10/
```

#### Response
```json
[
    {
        "rank": 1,
        "user_id": 42,
        "username": "player1",
        "total_score": 25000,
        "best_score": 5000,
        "games_played": 15,
        "last_played": "2024-01-15T10:30:00Z"
    }
]
```

#### Caching Strategy
```python
def get_top10_leaderboard(game_id):
    cache_key = f"leaderboard_top10_{game_id}"
    
    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Query database with window function
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                RANK() OVER (ORDER BY total_score DESC) as rank,
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
        
        results = cursor.fetchall()
    
    # Cache for 30 seconds
    cache.set(cache_key, results, 30)
    return results
```

## WebSocket Implementation

### Consumer Design
```python
class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'leaderboard_{self.game_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.send_initial_leaderboard()
    
    async def leaderboard_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'data': event['message']
        }))
```

### Message Types
```javascript
// Client to Server
{
    "type": "request_leaderboard"
}

{
    "type": "ping",
    "timestamp": 1640995200000
}

// Server to Client
{
    "type": "initial_leaderboard",
    "data": [...]
}

{
    "type": "leaderboard_update", 
    "data": {
        "user_id": 42,
        "username": "player1",
        "total_score": 15750
    }
}

{
    "type": "pong",
    "timestamp": 1640995200000
}
```

## Caching Strategy

### Cache Layers
```
┌─────────────────┐
│   Browser       │ ◄── Static assets (1 year)
│   Cache         │
└─────────────────┘
         │
┌─────────────────┐
│   CDN/Nginx     │ ◄── Frontend assets (1 year)
│   Cache         │     API responses (5 min)
└─────────────────┘
         │
┌─────────────────┐
│   Redis         │ ◄── Leaderboard data (30s)
│   Cache         │     Session data (1 hour)
└─────────────────┘
         │
┌─────────────────┐
│   MySQL         │ ◄── Persistent data
│   Database      │
└─────────────────┘
```

### Cache Keys
```python
CACHE_KEYS = {
    'leaderboard_top10': 'leaderboard_top10_{game_id}',
    'player_rank': 'player_rank_{game_id}_{user_id}',
    'game_stats': 'game_stats_{game_id}',
    'active_games': 'active_games'
}

CACHE_TIMEOUTS = {
    'leaderboard_top10': 30,  # 30 seconds
    'player_rank': 60,        # 1 minute
    'game_stats': 300,        # 5 minutes
    'active_games': 3600      # 1 hour
}
```

## Background Task Processing

### Celery Task Definitions
```python
@shared_task
def update_leaderboard_async(game_id):
    """Update rankings using MySQL window functions."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE leaderboard l1
            JOIN (
                SELECT id, 
                       RANK() OVER (ORDER BY total_score DESC) as new_rank
                FROM leaderboard 
                WHERE game_id = %s
            ) l2 ON l1.id = l2.id
            SET l1.rank = l2.new_rank
            WHERE l1.game_id = %s
        """, [game_id, game_id])
    
    cache.delete(f"leaderboard_top10_{game_id}")

@shared_task
def cleanup_old_sessions():
    """Clean up sessions older than 30 days."""
    cutoff_date = timezone.now() - timedelta(days=30)
    GameSession.objects.filter(
        session_start__lt=cutoff_date,
        is_completed=True
    ).delete()

@shared_task
def generate_daily_stats():
    """Generate daily statistics."""
    yesterday = timezone.now().date() - timedelta(days=1)
    # Generate and cache daily statistics
```

### Task Scheduling
```python
# celery-beat schedule
CELERY_BEAT_SCHEDULE = {
    'update-all-rankings': {
        'task': 'leaderboard.tasks.update_all_rankings',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-sessions': {
        'task': 'leaderboard.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-daily-stats': {
        'task': 'leaderboard.tasks.generate_daily_stats',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}
```

## Frontend Component Architecture

### Component Hierarchy
```
App
├── GameSelector
├── ScoreSubmission
│   ├── GameSelect
│   ├── ScoreInput
│   └── SubmitButton
├── Leaderboard
│   ├── LeaderboardHeader
│   ├── PlayerList
│   │   └── PlayerRow
│   └── RefreshButton
└── PlayerLookup
    ├── PlayerSelect
    ├── PlayerStats
    └── RankDisplay
```

### State Management
```javascript
// App.jsx state
const [selectedGame, setSelectedGame] = useState(null)
const [games, setGames] = useState([])
const [refreshTrigger, setRefreshTrigger] = useState(0)

// Leaderboard.jsx state  
const [leaderboard, setLeaderboard] = useState([])
const [wsService, setWsService] = useState(null)
const [isConnected, setIsConnected] = useState(false)

// WebSocket service
class WebSocketService {
    constructor(gameId) {
        this.gameId = gameId
        this.messageHandlers = new Map()
        this.reconnectAttempts = 0
    }
    
    connect() { /* WebSocket connection logic */ }
    subscribe(type, handler) { /* Message subscription */ }
    sendMessage(message) { /* Send message to server */ }
}
```

## Database Optimization

### Index Strategy
```sql
-- Query: Get top 10 players for a game
-- Uses: idx_leaderboard_game_total_score
SELECT * FROM leaderboard 
WHERE game_id = 1 
ORDER BY total_score DESC 
LIMIT 10;

-- Query: Get user sessions for a game
-- Uses: idx_game_sessions_user, idx_game_sessions_game_score
SELECT * FROM game_sessions 
WHERE user_id = 42 AND game_id = 1 
ORDER BY session_start DESC;

-- Query: Calculate player rank
-- Uses: idx_leaderboard_game_total_score with window function
SELECT RANK() OVER (ORDER BY total_score DESC) as rank
FROM leaderboard 
WHERE game_id = 1;
```

### Query Optimization
```python
# Use select_related for foreign keys
leaderboard = Leaderboard.objects.select_related(
    'user', 'game'
).filter(game_id=game_id).order_by('-total_score')[:10]

# Use prefetch_related for reverse foreign keys
users = User.objects.prefetch_related(
    'leaderboard_entries__game'
).filter(leaderboard_entries__game_id=game_id)

# Use database functions for aggregations
from django.db.models import Avg, Max, Sum
stats = GameSession.objects.filter(
    game_id=game_id
).aggregate(
    avg_score=Avg('score'),
    max_score=Max('score'),
    total_sessions=Count('id')
)
```

## Error Handling Strategy

### API Error Responses
```python
class APIErrorHandler:
    @staticmethod
    def handle_validation_error(error):
        return Response({
            'error': 'Validation failed',
            'details': error.detail
        }, status=400)
    
    @staticmethod  
    def handle_not_found(error):
        return Response({
            'error': 'Resource not found'
        }, status=404)
    
    @staticmethod
    def handle_server_error(error):
        logger.error(f"Server error: {error}")
        return Response({
            'error': 'Internal server error'
        }, status=500)
```

### Frontend Error Boundaries
```javascript
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }
    
    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }
    
    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo)
    }
    
    render() {
        if (this.state.hasError) {
            return <ErrorFallback error={this.state.error} />
        }
        return this.props.children
    }
}
```

## Testing Strategy

### Backend Tests
```python
# Model tests
class LeaderboardModelTest(TestCase):
    def test_get_user_rank(self):
        # Test ranking calculation
        
    def test_score_aggregation(self):
        # Test score totaling

# API tests  
class ScoreSubmissionTest(APITestCase):
    def test_submit_valid_score(self):
        # Test successful submission
        
    def test_submit_invalid_score(self):
        # Test validation errors

# Integration tests
class WebSocketTest(ChannelsTestCase):
    def test_leaderboard_updates(self):
        # Test real-time updates
```

### Frontend Tests
```javascript
// Component tests
describe('Leaderboard', () => {
    test('renders top 10 players', () => {
        // Test component rendering
    })
    
    test('handles WebSocket updates', () => {
        // Test real-time functionality
    })
})

// Integration tests
describe('Score Submission Flow', () => {
    test('submits score and updates leaderboard', () => {
        // Test end-to-end flow
    })
})
```

## Performance Monitoring

### Key Metrics
```python
# Custom middleware for performance tracking
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 1.0:
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        return response
```

### Database Query Monitoring
```python
# Django settings for query monitoring
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}

# Custom query analyzer
class QueryAnalyzer:
    @staticmethod
    def analyze_queries():
        from django.db import connection
        queries = connection.queries
        
        slow_queries = [
            q for q in queries 
            if float(q['time']) > 0.1
        ]
        
        return {
            'total_queries': len(queries),
            'slow_queries': len(slow_queries),
            'total_time': sum(float(q['time']) for q in queries)
        }
```
