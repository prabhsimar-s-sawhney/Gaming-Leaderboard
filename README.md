# Gaming Leaderboard 🎮🏆

A real-time gaming leaderboard application built with Django REST Framework and React, featuring live score updates, comprehensive statistics, and efficient caching.

![Build Status](https://github.com/username/gaming-leaderboard/workflows/CI/badge.svg)
![Coverage](https://codecov.io/gh/username/gaming-leaderboard/branch/main/graph/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **Real-time Updates**: Live score submissions and leaderboard updates via WebSockets
- **Multiple Games**: Support for multiple games with individual leaderboards  
- **Player Statistics**: Comprehensive player rankings, scores, and game history
- **Performance Optimized**: Redis caching, database indexing, and query optimization
- **Responsive Design**: Beautiful, mobile-first UI with Tailwind CSS
- **Scalable Architecture**: Microservice-ready with Docker containerization

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js 18+ (for local development)
- MySQL 8.0+
- Redis 7+

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/username/gaming-leaderboard.git
   cd gaming-leaderboard
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

4. **Create sample data**
   ```bash
   docker-compose exec backend python manage.py shell -c "
   from leaderboard.models import Game
   Game.objects.get_or_create(name='Space Invaders', defaults={'description': 'Classic arcade game'})
   Game.objects.get_or_create(name='Tetris', defaults={'description': 'Block puzzle game'})
   "
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/
   - Admin Panel: http://localhost:8000/admin/

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export DEBUG=True
export DB_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

# Run migrations and start server
python manage.py migrate
python manage.py runserver
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React SPA     │    │   Django API     │    │    MySQL DB     │
│   (Frontend)    │◄──►│   (Backend)      │◄──►│  (Primary DB)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       
         │              ┌──────────────────┐             
         │              │     Redis        │             
         │              │  (Cache & Queue) │             
         │              └──────────────────┘             
         │                       │                       
         │              ┌──────────────────┐             
         └──────────────►│   WebSockets     │             
                        │  (Real-time)     │             
                        └──────────────────┘             
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React 18 + Vite + Tailwind | User interface |
| Backend | Django 4.x + DRF | REST API |
| Real-time | Django Channels | WebSocket support |
| Database | MySQL 8.0 | Primary data storage |
| Cache | Redis 7 | Caching and queuing |
| Background Jobs | Celery | Async task processing |
| Monitoring | New Relic | APM and analytics |
| Deployment | Docker + Compose | Containerization |

## 📊 API Endpoints

### Games
- `GET /api/games/` - List all active games

### Score Submission  
- `POST /api/submit-score/` - Submit a player score
  ```json
  {
    "game_id": 1,
    "score": 1500,
    "user_id": 42
  }
  ```

### Leaderboard
- `GET /api/leaderboard/{game_id}/top10/` - Get top 10 players
- `GET /api/leaderboard/{game_id}/player/{user_id}/` - Get player rank

### WebSocket
- `ws://api/ws/leaderboard/{game_id}/` - Real-time leaderboard updates

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python manage.py test
coverage run --source='.' manage.py test
coverage report
```

### Run Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up -d
python scripts/smoke_tests.py
```

### Performance Tests
```bash
pip install locust
locust -f scripts/locustfile.py --host=http://localhost:8000
```

## 🛠️ Development

### Project Structure
```
gaming-leaderboard/
├── backend/                    # Django backend
│   ├── gaming_leaderboard/    # Project settings
│   ├── leaderboard/           # Main app
│   │   ├── models.py         # Database models
│   │   ├── views.py          # API views
│   │   ├── serializers.py    # DRF serializers
│   │   ├── tasks.py          # Celery tasks
│   │   └── consumers.py      # WebSocket consumers
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   └── App.jsx          # Main app component
│   └── package.json         # Node.js dependencies
├── scripts/                  # Utility scripts
│   ├── simulate.py          # Data simulation
│   └── smoke_tests.py       # Integration tests
├── docker-compose.yml       # Docker services
└── .github/workflows/       # CI/CD pipelines
```

### Database Schema

#### Core Models
- **Game**: Stores game information
- **GameSession**: Individual game sessions and scores  
- **Leaderboard**: Aggregated player rankings and statistics

#### Key Relationships
```sql
User (Django) ──┐
                ├─► GameSession ──► Game
                └─► Leaderboard ──┘
```

### Caching Strategy

- **Leaderboard Top 10**: 30-second cache
- **Player Rankings**: 1-minute cache  
- **Game List**: 1-hour cache
- **WebSocket**: Real-time invalidation

## 🚀 Deployment

### Production Deployment

1. **Environment Variables**
   ```bash
   SECRET_KEY=your-production-secret
   DEBUG=False
   DB_HOST=your-mysql-host
   DB_PASSWORD=your-db-password
   REDIS_URL=redis://your-redis-host:6379/0
   ```

2. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```

3. **Service Health Checks**
   - Backend: `GET /api/games/`
   - Database: Connection test
   - Redis: Ping test
   - WebSocket: Connection test

### CI/CD Pipeline

The project includes a comprehensive GitHub Actions workflow:

- ✅ Automated testing (backend + frontend)
- 🔒 Security scanning with Trivy
- 🐳 Docker image building and pushing  
- 🧪 Integration and performance testing
- 🚀 Automated deployment to staging/production

## 📈 Performance

### Benchmarks
- **API Response Time**: < 200ms (95th percentile)
- **Page Load Time**: < 2s (First Contentful Paint)
- **WebSocket Latency**: < 100ms
- **Concurrent Users**: 10,000+
- **Score Submissions**: 1,000+/minute

### Optimization Features
- Database indexing on critical queries
- Redis caching with intelligent invalidation
- Connection pooling and query optimization
- Static asset optimization with CDN
- Real-time updates via WebSockets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript
- Write tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Real-time leaderboard
- ✅ Score submission
- ✅ Player rankings
- ✅ WebSocket integration

### Phase 2 (Planned)
- 🔄 User authentication system
- 🔄 Tournament support
- 🔄 Advanced analytics dashboard
- 🔄 Mobile app development

### Phase 3 (Future)
- 🔮 Machine learning recommendations
- 🔮 Multi-region support
- 🔮 Advanced game mechanics
- 🔮 Social features

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/username/gaming-leaderboard/wiki)
- **Issues**: [GitHub Issues](https://github.com/username/gaming-leaderboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/gaming-leaderboard/discussions)

## 👏 Acknowledgments

- Django and React communities
- Tailwind CSS for beautiful styling
- Docker for containerization
- All contributors and testers

---

<div align="center">
  <strong>Built with ❤️ for the gaming community</strong>
</div>
