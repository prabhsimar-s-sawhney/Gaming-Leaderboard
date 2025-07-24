-- Initialize database with optimal settings for gaming leaderboard
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Create indexes for better performance
-- Note: Django migrations will create these, but having them here as reference

-- Games table
CREATE INDEX IF NOT EXISTS idx_games_active ON games(is_active);
CREATE INDEX IF NOT EXISTS idx_games_created ON games(created_at);

-- Game sessions table  
CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_game_score ON game_sessions(game_id, score);
CREATE INDEX IF NOT EXISTS idx_game_sessions_start ON game_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_game_sessions_completed ON game_sessions(is_completed);

-- Leaderboard table
CREATE INDEX IF NOT EXISTS idx_leaderboard_game_total_score ON leaderboard(game_id, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_game_best_score ON leaderboard(game_id, best_score DESC);
CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON leaderboard(rank);
CREATE INDEX IF NOT EXISTS idx_leaderboard_last_played ON leaderboard(last_played);

-- Create sample games
INSERT IGNORE INTO games (id, name, description, is_active, created_at) VALUES
(1, 'Space Invaders', 'Classic arcade space shooter game', 1, NOW()),
(2, 'Tetris', 'Block-stacking puzzle game', 1, NOW()),
(3, 'Pac-Man', 'Classic maze chase game', 1, NOW()),
(4, 'Snake', 'Classic snake growing game', 1, NOW()),
(5, 'Asteroids', 'Space shooting game with asteroids', 1, NOW());

-- Create sample users (Django will handle user creation, but this is for reference)
-- Users will be created via Django management commands or admin interface
