import React, { useState, useEffect, useRef } from 'react'
import { leaderboardService, WebSocketService, formatScore, formatDateTime, getRankEmoji, getRankColor } from '../services/api'

const Leaderboard = ({ gameId, gameName, refreshTrigger }) => {
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [wsService, setWsService] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const currentGameIdRef = useRef(gameId)

  useEffect(() => {
    currentGameIdRef.current = gameId
    
    if (gameId) {
      // Clear existing state when game changes
      setLeaderboard([])
      setError(null)
      setIsConnected(false)
      setLastUpdate(null)
      
      loadLeaderboard()
      setupWebSocket()
    }

    return () => {
      if (wsService) {
        wsService.stopHeartbeat()
        wsService.disconnect()
      }
    }
  }, [gameId])

  useEffect(() => {
    if (refreshTrigger > 0) {
      loadLeaderboard()
    }
  }, [refreshTrigger])

  const loadLeaderboard = async () => {
    const requestGameId = currentGameIdRef.current
    if (!requestGameId) {
      console.warn('No gameId provided for loadLeaderboard')
      return
    }

    try {
      setLoading(true)
      console.log(`Loading leaderboard for game ${requestGameId}`)
      const response = await leaderboardService.getTop10(requestGameId)
      
      // Only update state if we're still looking at the same game
      if (requestGameId === currentGameIdRef.current) {
        setLeaderboard(response.data || [])
        setLastUpdate(new Date())
        setError(null)
        console.log(`Leaderboard loaded for game ${requestGameId}:`, response.data?.length || 0, 'entries')
      } else {
        console.warn(`Ignoring leaderboard response for game ${requestGameId}, component has moved to game ${currentGameIdRef.current}`)
      }
    } catch (err) {
      console.error(`Failed to load leaderboard for game ${requestGameId}:`, err)
      if (requestGameId === currentGameIdRef.current) {
        setError('Failed to load leaderboard data')
      }
    } finally {
      setLoading(false)
    }
  }

  const setupWebSocket = () => {
    // Clean up existing connection first
    if (wsService) {
      console.log(`Cleaning up existing WebSocket connection for game ${wsService.gameId}`)
      wsService.stopHeartbeat()
      wsService.disconnect()
      setWsService(null)
      setIsConnected(false)
    }

    console.log(`Setting up new WebSocket connection for game ${gameId}`)
    const ws = new WebSocketService(gameId)
    setWsService(ws)

    // Handle WebSocket messages
    ws.subscribe('initial_leaderboard', (data) => {
      console.log(`Received initial leaderboard for game ${gameId}:`, data.data)
      // Verify this message is for the current game
      if (ws.gameId === currentGameIdRef.current) {
        setLeaderboard(data.data || [])
        setLastUpdate(new Date())
        setIsConnected(true)
      } else {
        console.warn(`Ignoring leaderboard data for game ${ws.gameId}, current game is ${currentGameIdRef.current}`)
      }
    })

    ws.subscribe('leaderboard_update', (data) => {
      console.log(`Received leaderboard update for game ${gameId}:`, data.data)
      // Verify this message is for the current game
      if (ws.gameId === currentGameIdRef.current) {
        // Refresh leaderboard data
        loadLeaderboard()
        setLastUpdate(new Date())
      } else {
        console.warn(`Ignoring leaderboard update for game ${ws.gameId}, current game is ${currentGameIdRef.current}`)
      }
    })

    ws.subscribe('pong', (data) => {
      console.log(`WebSocket pong received for game ${gameId}`)
    })

    ws.subscribe('error', (data) => {
      console.error(`WebSocket error for game ${gameId}:`, data.message)
      if (ws.gameId === currentGameIdRef.current) {
        setError(data.message)
      }
    })

    // Connect and start heartbeat
    ws.connect()
    ws.startHeartbeat()
  }

  const handleRefresh = () => {
    loadLeaderboard()
  }

  if (loading && leaderboard.length === 0) {
    return (
      <div className="card p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto"></div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card p-8 card-hover">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-black gradient-text tracking-tight">
            👑 Rankings
          </h2>
          <p className="text-luxury-light mt-2 font-medium">
            {gameName} • {leaderboard.length} competitors
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2 text-sm">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-luxury-light font-medium">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
          
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="p-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-gray-300/50 shadow-md hover:shadow-lg"
            title="Refresh leaderboard"
          >
            <svg 
              className={`w-5 h-5 text-luxury ${loading ? 'animate-spin' : ''}`} 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <div className="text-xs text-luxury-light mb-6 text-center font-medium">
          Last updated: {formatDateTime(lastUpdate.toISOString())}
        </div>
      )}

      {/* Error State */}
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

      {/* Leaderboard List */}
      {leaderboard.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-6">🎮</div>
          <h3 className="text-xl font-bold text-luxury-dark mb-3">No competitors yet</h3>
          <p className="text-luxury-light">Be the first to claim your throne!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {leaderboard.map((player, index) => (
            <div
              key={`${player.user_id}-${player.rank}`}
              className={`flex items-center p-6 rounded-xl transition-all duration-300 hover:scale-[1.01] shadow-md hover:shadow-lg ${
                index < 3 ? 'bg-gradient-to-r from-gray-50 to-white border-2 border-gray-300' : 'bg-white border border-gray-200'
              }`}
            >
              {/* Rank */}
              <div className={`flex items-center justify-center w-14 h-14 rounded-full font-bold text-lg mr-6 ${getRankColor(player.rank)} shadow-lg`}>
                <span className="mr-1">{getRankEmoji(player.rank)}</span>
                <span>{player.rank}</span>
              </div>

              {/* Player Info */}
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="font-bold text-luxury-dark text-lg tracking-wide">
                    {player.username}
                  </h3>
                </div>
                
                <div className="flex items-center space-x-6 text-sm text-luxury-light mt-2 font-medium">
                  <span>🎯 Best: {formatScore(player.best_score)}</span>
                  <span>🎮 Games: {player.games_played}</span>
                  <span>⏰ {formatDateTime(player.last_played)}</span>
                </div>
              </div>

              {/* Score */}
              <div className="text-right">
                <div className="text-3xl font-black gradient-text tracking-tight">
                  {formatScore(player.total_score)}
                </div>
                <div className="text-xs text-luxury-light font-medium tracking-wide">total score</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-200 text-center">
        <p className="text-xs text-luxury-light font-medium tracking-wide">
          🔄 Real-time updates • 👑 Rankings refresh automatically
        </p>
      </div>
    </div>
  )
}

export default Leaderboard
