import React, { useState, useEffect, useRef } from 'react'
import { userService } from '../services/api'

const UserSelector = ({ selectedUserId, onUserSelect, label = "Select Player", required = true }) => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  
  const dropdownRef = useRef(null)
  const searchInputRef = useRef(null)
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Load initial users
  useEffect(() => {
    loadUsers()
  }, [])
  
  // Load users when search changes (with debounce)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setPage(1)
      loadUsers(searchQuery, 1)
    }, 300)
    
    return () => clearTimeout(timeoutId)
  }, [searchQuery])
  
  // Find selected user when selectedUserId changes
  useEffect(() => {
    if (selectedUserId && users.length > 0) {
      const user = users.find(u => u.id.toString() === selectedUserId.toString())
      setSelectedUser(user)
    }
  }, [selectedUserId, users])
  
  const loadUsers = async (search = '', pageNum = 1, append = false) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await userService.searchUsers(search, pageNum, 10)
      const { users: newUsers, pagination: newPagination } = response.data
      
      if (append) {
        setUsers(prev => [...prev, ...newUsers])
      } else {
        setUsers(newUsers)
      }
      
      setPagination(newPagination)
      setPage(pageNum)
    } catch (err) {
      console.error('Failed to load users:', err)
      setError('Failed to load users')
    } finally {
      setLoading(false)
    }
  }
  
  const handleLoadMore = () => {
    if (pagination && pagination.has_next && !loading) {
      loadUsers(searchQuery, page + 1, true)
    }
  }
  
  const handleUserSelect = (user) => {
    setSelectedUser(user)
    setIsDropdownOpen(false)
    setSearchQuery('')
    onUserSelect(user.id, user)
  }
  
  const handleDropdownToggle = () => {
    setIsDropdownOpen(!isDropdownOpen)
    if (!isDropdownOpen) {
      // Reset search when opening
      setSearchQuery('')
      setPage(1)
      loadUsers()
      // Focus search input after dropdown opens
      setTimeout(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus()
        }
      }, 100)
    }
  }
  
  const displayName = selectedUser 
    ? `${selectedUser.username}${selectedUser.first_name ? ` (${selectedUser.first_name})` : ''}`
    : 'Select a player...'

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-bold text-luxury-dark mb-3 tracking-wide">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      
      {/* Selected User Display */}
      <button
        type="button"
        onClick={handleDropdownToggle}
        className="input-field w-full text-left flex items-center justify-between hover:border-gray-400 transition-all duration-300"
      >
        <span className={selectedUser ? 'text-luxury-dark font-medium' : 'text-luxury-light'}>
          {displayName}
        </span>
        <svg 
          className={`w-5 h-5 text-luxury-light transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {/* Dropdown */}
      {isDropdownOpen && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-300 rounded-xl shadow-2xl max-h-80 flex flex-col">
          {/* Search Input */}
          <div className="p-4 border-b border-gray-200">
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search competitors..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-4 focus:ring-gray-400/30 focus:border-gray-500 transition-all duration-300 text-sm font-medium"
            />
          </div>
          
          {/* Users List */}
          <div className="flex-1 overflow-y-auto">
            {error && (
              <div className="p-4 text-red-600 text-sm font-medium">
                {error}
              </div>
            )}
            
            {loading && users.length === 0 ? (
              <div className="p-4 text-luxury-light text-sm font-medium">
                Loading competitors...
              </div>
            ) : users.length === 0 ? (
              <div className="p-4 text-luxury-light text-sm font-medium">
                {searchQuery ? 'No competitors found matching your search.' : 'No competitors available.'}
              </div>
            ) : (
              <>
                {users.map((user) => (
                  <button
                    key={user.id}
                    type="button"
                    onClick={() => handleUserSelect(user)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-all duration-300 text-sm ${
                      selectedUser && selectedUser.id === user.id ? 'bg-gray-100 text-luxury-dark border-r-4 border-gray-800' : 'text-luxury'
                    }`}
                  >
                    <div className="font-bold tracking-wide">{user.username}</div>
                    {user.first_name && (
                      <div className="text-xs text-luxury-light font-medium">{user.first_name} {user.last_name || ''}</div>
                    )}
                  </button>
                ))}
                
                {/* Load More Button */}
                {pagination && pagination.has_next && (
                  <div className="p-4 border-t border-gray-200">
                    <button
                      type="button"
                      onClick={handleLoadMore}
                      disabled={loading}
                      className="w-full px-4 py-2 text-sm text-luxury hover:text-luxury-dark disabled:text-luxury-light disabled:cursor-not-allowed font-semibold transition-colors duration-300"
                    >
                      {loading ? 'Loading...' : `Load More (${pagination.total_count - users.length} remaining)`}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
          
          {/* Pagination Info */}
          {pagination && users.length > 0 && (
            <div className="p-3 border-t border-gray-200 text-xs text-luxury-light text-center font-medium">
              Showing {users.length} of {pagination.total_count} competitors
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default UserSelector
