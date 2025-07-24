import React, { useState } from 'react'
import { leaderboardService } from '../services/api'
import UserSelector from './UserSelector'

const SubmitScore = ({ games, selectedGame, onScoreSubmitted }) => {
  const [score, setScore] = useState('')
  const [userId, setUserId] = useState(null) // No default user
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!selectedGame) {
      setError('Please select a game')
      return
    }

    if (!userId) {
      setError('Please select a player')
      return
    }

    if (!score || parseInt(score) < 0) {
      setError('Please enter a valid score (0 or higher)')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const response = await leaderboardService.submitScore(
        selectedGame.id,
        parseInt(score),
        parseInt(userId)
      )

      console.log('Score submitted successfully:', response.data)
      setSuccess(true)
      setScore('')
      
      // Trigger refresh in parent components
      if (onScoreSubmitted) {
        onScoreSubmitted()
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000)

    } catch (err) {
      console.error('Failed to submit score:', err)
      setError(
        err.response?.data?.error || 
        err.response?.data?.message || 
        'Failed to submit score. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card p-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black gradient-text mb-3 tracking-tight">
          ⚡ Submit Performance
        </h2>
        <p className="text-luxury-light font-medium">
          {selectedGame ? `Competing in ${selectedGame.name}` : 'Select a championship to continue'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Game Info */}
        {selectedGame && (
          <div className="bg-gradient-to-r from-gray-50 to-white p-6 rounded-xl border border-gray-200">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🎮</div>
              <div>
                <h3 className="font-bold text-luxury-dark tracking-wide">{selectedGame.name}</h3>
                <p className="text-sm text-luxury-light font-medium">{selectedGame.description}</p>
              </div>
            </div>
          </div>
        )}

        {/* User Selection */}
        <UserSelector
          selectedUserId={userId}
          onUserSelect={(id, user) => setUserId(id.toString())}
          label="Player"
          required={true}
        />

        {/* Score Input */}
        <div>
          <label htmlFor="score" className="block text-sm font-bold text-luxury-dark mb-3 tracking-wide">
            Performance Score
          </label>
          <div className="flex space-x-3">
            <input
              type="number"
              id="score"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              min="0"
              max="1000000"
              placeholder="Enter your score"
              className="input-field flex-1"
              required
            />
          </div>
          <p className="text-xs text-luxury-light mt-2 font-medium">
            Enter a score between 0 and 1,000,000
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-red-800 text-sm font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-green-800 text-sm font-medium">Performance submitted successfully! 🎉</span>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !selectedGame || !userId}
          className={`w-full button-primary ${
            loading || !selectedGame || !userId
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:scale-105'
          }`}
        >
          {loading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Submitting...</span>
            </div>
          ) : (
            <div className="flex items-center justify-center space-x-2">
              <span>🚀</span>
              <span>Submit Performance</span>
            </div>
          )}
        </button>
      </form>

      {/* Tips */}
      <div className="mt-8 p-6 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-200">
        <h3 className="font-bold text-luxury-dark mb-3 tracking-wide">� Pro Tips:</h3>
        <ul className="text-sm text-luxury-light space-y-2 font-medium">
          <li>• Superior performance elevates your championship standing</li>
          <li>• Personal records are preserved automatically</li>
          <li>• Rankings update instantaneously across all platforms</li>
        </ul>
      </div>
    </div>
  )
}

export default SubmitScore
