import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// Game Service
export const gameService = {
  async getGames() {
    try {
      const response = await apiClient.get('/games/')
      return response
    } catch (error) {
      console.error('Error fetching games:', error)
      throw error
    }
  }
}

// User Service
export const userService = {
  async searchUsers(searchQuery = '', page = 1, pageSize = 10) {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      })
      
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim())
      }
      
      const response = await apiClient.get(`/users/search/?${params}`)
      return response
    } catch (error) {
      console.error('Error searching users:', error)
      throw error
    }
  }
}

// Leaderboard Service
export const leaderboardService = {
  async getTop10(gameId) {
    try {
      const response = await apiClient.get(`/leaderboard/${gameId}/top10/`)
      return response
    } catch (error) {
      console.error('Error fetching top 10:', error)
      throw error
    }
  },

  async getPlayerRank(gameId, userId) {
    try {
      const response = await apiClient.get(`/leaderboard/${gameId}/player/${userId}/`)
      return response
    } catch (error) {
      console.error('Error fetching player rank:', error)
      throw error
    }
  },

  async submitScore(gameId, score, userId = 1) {
    try {
      const response = await apiClient.post('/submit-score/', {
        game_id: gameId,
        score: score,
        user_id: userId
      })
      return response
    } catch (error) {
      console.error('Error submitting score:', error)
      throw error
    }
  }
}

// WebSocket Service
export class WebSocketService {
  constructor(gameId) {
    this.gameId = gameId
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.isConnected = false
    this.messageHandlers = new Map()
    this.isDisconnected = false // Add flag to prevent reconnection after manual disconnect
  }

  connect() {
    if (this.isDisconnected) {
      console.log(`WebSocket for game ${this.gameId} is manually disconnected, skipping connect`)
      return
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/leaderboard/${this.gameId}/`
      console.log(`Connecting to WebSocket: ${wsUrl}`)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log(`WebSocket connected for game ${this.gameId}`)
        this.isConnected = true
        this.reconnectAttempts = 0
        this.sendMessage({ type: 'request_leaderboard' })
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log(`WebSocket closed for game ${this.gameId}:`, event.code, event.reason)
        this.isConnected = false
        
        // Only attempt reconnection if not manually disconnected
        if (!this.isDisconnected && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          setTimeout(() => this.connect(), this.reconnectInterval)
        }
      }

      this.ws.onerror = (error) => {
        console.error(`WebSocket error for game ${this.gameId}:`, error)
      }

    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
    }
  }

  handleMessage(data) {
    const { type } = data
    const handler = this.messageHandlers.get(type)
    
    if (handler) {
      handler(data)
    } else {
      console.log('Unhandled WebSocket message:', data)
    }
  }

  sendMessage(message) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(message))
    }
  }

  subscribe(messageType, handler) {
    this.messageHandlers.set(messageType, handler)
  }

  unsubscribe(messageType) {
    this.messageHandlers.delete(messageType)
  }

  disconnect() {
    console.log(`Manually disconnecting WebSocket for game ${this.gameId}`)
    this.isDisconnected = true // Set flag to prevent reconnection
    this.isConnected = false
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect') // Normal closure
      this.ws = null
    }
    
    // Clear message handlers
    this.messageHandlers.clear()
  }

  ping() {
    this.sendMessage({
      type: 'ping',
      timestamp: Date.now()
    })
  }

  // Start periodic ping to keep connection alive
  startHeartbeat(interval = 30000) {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.ping()
      }
    }, interval)
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
    }
  }
}

// Utility functions
export const formatScore = (score) => {
  return score.toLocaleString()
}

export const formatDateTime = (dateString) => {
  if (!dateString) return 'Never'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInMinutes = Math.floor((now - date) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  
  return date.toLocaleDateString()
}

export const getRankEmoji = (rank) => {
  switch (rank) {
    case 1: return '🥇'
    case 2: return '🥈'  
    case 3: return '🥉'
    default: return '🏅'
  }
}

export const getRankColor = (rank) => {
  switch (rank) {
    case 1: return 'text-yellow-600 bg-yellow-50'
    case 2: return 'text-gray-600 bg-gray-50'
    case 3: return 'text-orange-600 bg-orange-50'
    default: return 'text-purple-600 bg-purple-50'
  }
}
