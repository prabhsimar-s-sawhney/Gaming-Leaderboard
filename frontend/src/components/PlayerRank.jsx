import React, { useState, useEffect } from 'react'
import { leaderboardService, formatScore, formatDateTime, getRankEmoji, getRankColor } from '../services/api'
import UserSelector from './UserSelector'

const PlayerRank = ({ gameId, refreshTrigger }) => {
  const [playerData, setPlayerData] = useState(null)
  const [selectedUserId, setSelectedUserId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)

  useEffect(() => {
    if (refreshTrigger > 0 && playerData) {
      // Auto-refresh if we have previously searched for a player
      handleLookup()
    }
  }, [refreshTrigger])

  const handleLookup = async () => {
    if (!gameId || !selectedUserId) {
      setError('Please select a valid player and game')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await leaderboardService.getPlayerRank(gameId, parseInt(selectedUserId))
      setPlayerData(response.data)
      setSearched(true)
    } catch (err) {
      console.error('Failed to fetch player rank:', err)
      setError(
        err.response?.data?.error || 
        'Failed to fetch player information. Please try again.'
      )
      setPlayerData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black gradient-text mb-3 tracking-tight">
          🔍 Search
        </h2>
        <p className="text-luxury-light font-medium">
          Discover competitor rankings and performance metrics
        </p>
      </div>

      {/* Player Selection */}
      <div className="flex space-x-4 mb-8">
        <div className="flex-1">
          <UserSelector
            selectedUserId={selectedUserId}
            onUserSelect={(id, user) => setSelectedUserId(id.toString())}
            label="Select Competitor"
            required={false}
          />
        </div>
        
        <div className="flex items-end">
          <button
            onClick={handleLookup}
            disabled={loading || !gameId || !selectedUserId}
            className={`button-primary ${
              loading || !gameId || !selectedUserId
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:scale-105'
            }`}
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Analyzing...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <span>🔍</span>
                <span>Analyze</span>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800 text-sm font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Player Data */}
      {searched && playerData && (
        <div className="space-y-8">
          {/* Player Header */}
          <div className="bg-gradient-to-r from-gray-50 to-white p-8 rounded-xl border border-gray-200 shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <div className="w-20 h-20 bg-gradient-to-r from-gray-800 to-black rounded-full flex items-center justify-center text-white text-3xl font-black shadow-lg">
                  {playerData.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-3xl font-black text-luxury-dark tracking-tight">
                    {playerData.username}
                  </h3>
                  <p className="text-luxury-light font-medium text-lg">
                    Competing in {playerData.game_name}
                  </p>
                </div>
              </div>
              
              {/* Rank Badge */}
              {playerData.rank ? (
                <div className={`flex items-center px-6 py-3 rounded-xl font-bold text-lg shadow-lg ${getRankColor(playerData.rank)}`}>
                  <span className="mr-2">{getRankEmoji(playerData.rank)}</span>
                  <span>Rank #{playerData.rank}</span>
                </div>
              ) : (
                <div className="px-6 py-3 bg-gray-100 rounded-xl shadow-md">
                  <span className="text-luxury font-bold">Unranked</span>
                </div>
              )}
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Score */}
            <div className="bg-gradient-to-br from-gray-100 to-white p-6 rounded-xl shadow-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-luxury-dark text-sm font-bold tracking-wide">Total Score</span>
                <span className="text-3xl">🎯</span>
              </div>
              <div className="text-3xl font-black text-luxury-dark">
                {formatScore(playerData.total_score)}
              </div>
            </div>

            {/* Best Score */}
            <div className="bg-gradient-to-br from-gray-100 to-white p-6 rounded-xl shadow-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-luxury-dark text-sm font-bold tracking-wide">Best Score</span>
                <span className="text-3xl">⭐</span>
              </div>
              <div className="text-3xl font-black text-luxury-dark">
                {formatScore(playerData.best_score)}
              </div>
            </div>

            {/* Games Played */}
            <div className="bg-gradient-to-br from-gray-100 to-white p-6 rounded-xl shadow-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-luxury-dark text-sm font-bold tracking-wide">Games Played</span>
                <span className="text-3xl">🎮</span>
              </div>
              <div className="text-3xl font-black text-luxury-dark">
                {playerData.games_played}
              </div>
            </div>

            {/* Average Score */}
            <div className="bg-gradient-to-br from-gray-100 to-white p-6 rounded-xl shadow-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-luxury-dark text-sm font-bold tracking-wide">Average Score</span>
                <span className="text-3xl">📊</span>
              </div>
              <div className="text-3xl font-black text-luxury-dark">
                {playerData.games_played > 0 
                  ? formatScore(Math.round(playerData.total_score / playerData.games_played))
                  : '0'
                }
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h4 className="font-bold text-luxury-dark mb-4 tracking-wide">📅 Activity Analysis</h4>
            <div className="flex items-center justify-between text-sm">
              <span className="text-luxury-light font-medium">Last Performance:</span>
              <span className="font-bold text-luxury-dark">
                {formatDateTime(playerData.last_played)}
              </span>
            </div>
          </div>

          {/* Rank Analysis */}
          {playerData.rank && (
            <div className="bg-gradient-to-r from-gray-50 to-white p-6 rounded-xl shadow-lg border border-gray-200">
              <h4 className="font-bold text-luxury-dark mb-3 tracking-wide">🏆 Player Analysis</h4>
              <div className="text-sm text-luxury-light space-y-2 font-medium">
                {playerData.rank === 1 && (
                  <p className="text-yellow-700 font-bold">🥇 Supreme! This competitor dominates the leaderboard!</p>
                )}
                {playerData.rank <= 3 && playerData.rank > 1 && (
                  <p className="text-luxury-dark font-bold">🏅 Exceptional! Elite tier performance!</p>
                )}
                {playerData.rank <= 10 && playerData.rank > 3 && (
                  <p className="text-luxury font-bold">⭐ Outstanding! Top-tier competitor!</p>
                )}
                {playerData.rank > 10 && (
                  <p className="text-luxury">📈 Continue competing to ascend the rankings!</p>
                )}
              </div>
            </div>
          )}

          {playerData.games_played === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎮</div>
              <h3 className="text-xl font-bold text-luxury-dark mb-3">
                No competitions entered
              </h3>
              <p className="text-luxury-light text-sm font-medium">
                This competitor hasn't submitted any performances for this championship
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {searched && !playerData && !error && !loading && (
        <div className="text-center py-12">
          <div className="text-6xl mb-6">👤</div>
          <h3 className="text-xl font-bold text-luxury-dark mb-3">
            Competitor not found
          </h3>
          <p className="text-luxury-light font-medium">
            This competitor hasn't entered this championship yet
          </p>
        </div>
      )}

      {/* Instructions */}
      {!searched && !loading && (
        <div className="text-center py-12">
          <div className="text-6xl mb-6">🔍</div>
          <h3 className="text-xl font-bold text-luxury-dark mb-3">
            Competitor analysis
          </h3>
          <p className="text-luxury-light font-medium">
            Select a competitor and click "Analyze" to view their performance metrics
          </p>
        </div>
      )}
    </div>
  )
}

export default PlayerRank
