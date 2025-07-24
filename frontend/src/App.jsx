import React, { useState, useEffect } from 'react'
import Leaderboard from './components/Leaderboard'
import SubmitScore from './components/SubmitScore'
import PlayerRank from './components/PlayerRank'
import { gameService } from './services/api'

function App() {
  const [selectedGame, setSelectedGame] = useState(null)
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    loadGames()
  }, [])

  const loadGames = async () => {
    try {
      setLoading(true)
      const response = await gameService.getGames()
      setGames(response.data || [])
      if (response.data && response.data.length > 0) {
        setSelectedGame(response.data[0])
      }
      setError(null)
    } catch (err) {
      console.error('Failed to load games:', err)
      setError('Failed to load games. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleScoreSubmitted = () => {
    // Trigger refresh of leaderboard components
    setRefreshTrigger(prev => prev + 1)
  }

  if (loading) {
    return (
      <div className="min-h-screen luxury-gradient flex items-center justify-center">
        <div className="card p-8">
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-800"></div>
            <span className="text-luxury font-medium">Loading games...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen luxury-gradient flex items-center justify-center">
        <div className="card p-8 text-center">
          <div className="text-red-600 mb-4">
            <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-luxury-dark mb-2">Something went wrong</h2>
          <p className="text-luxury-light mb-4">{error}</p>
          <button 
            onClick={loadGames}
            className="button-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen luxury-gradient">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-6xl font-black gradient-text mb-4 animate-fade-in tracking-tight">
            ⚡ Gaming Leaderboard
          </h1>
          <p className="text-xl text-luxury-light font-medium tracking-wide">
            Elite competitive gaming rankings
          </p>
        </header>

        {/* Game Selection */}
        {games.length > 0 && (
          <div className="mb-8">
            <div className="card p-8 max-w-4xl mx-auto">
              <h2 className="text-2xl font-bold text-luxury-dark mb-6 text-center tracking-wide">
                Select Championship
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {games.map((game) => (
                  <button
                    key={game.id}
                    onClick={() => setSelectedGame(game)}
                    className={`p-6 rounded-xl font-semibold transition-all duration-300 transform ${
                      selectedGame?.id === game.id
                        ? 'bg-gradient-to-r from-gray-900 to-black text-white shadow-2xl scale-105 border border-gray-700'
                        : 'bg-gray-50 text-luxury hover:bg-white hover:scale-102 shadow-md hover:shadow-lg border border-gray-200'
                    }`}
                  >
                    🎮 {game.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedGame && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Submit Score */}
            <div className="lg:col-span-1">
              <SubmitScore 
                games={games} 
                selectedGame={selectedGame}
                onScoreSubmitted={handleScoreSubmitted}
              />
            </div>

            {/* Leaderboard */}
            <div className="lg:col-span-2">
              <Leaderboard 
                gameId={selectedGame.id} 
                gameName={selectedGame.name}
                refreshTrigger={refreshTrigger}
              />
            </div>
          </div>
        )}

        {selectedGame && (
          <div className="mt-8">
            <PlayerRank 
              gameId={selectedGame.id}
              refreshTrigger={refreshTrigger}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default App
