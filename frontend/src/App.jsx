import { useState } from 'react'
import PRForm from './components/PRForm'
import DiffForm from './components/DiffForm'
import ReviewCard from './components/ReviewCard'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('pr')

  const handlePRSubmit = async (data) => {
    setLoading(true)
    setError(null)
    setReviews([])

    try {
      // Split repo into owner and name
      const [repo_owner, repo_name] = data.repo.split('/')
      
      if (!repo_owner || !repo_name) {
        throw new Error('Repository must be in format "owner/repo"')
      }

      const payload = {
        repo_owner,
        repo_name,
        pr_number: data.pr_number,
        github_token: data.github_token
      }

      const response = await fetch(`${API_BASE_URL}/review/pr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.error?.message || errorData.detail || `Error: ${response.statusText}`
        throw new Error(errorMsg)
      }

      const result = await response.json()
      setReviews(result.comments || result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDiffSubmit = async (data) => {
    setLoading(true)
    setError(null)
    setReviews([])

    try {
      const response = await fetch(`${API_BASE_URL}/review/diff`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.error?.message || errorData.detail || `Error: ${response.statusText}`
        throw new Error(errorMsg)
      }

      const result = await response.json()
      setReviews(result.comments || result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(reviews, null, 2))
      .then(() => alert('JSON copied to clipboard!'))
      .catch(() => alert('Failed to copy'))
  }

  return (
    <div className="app">
      <header>
        <h1>Automated PR Review Agent</h1>
        <p>Analyze GitHub Pull Requests or raw diffs using AI-powered code review</p>
      </header>

      <div className="tabs">
        <button
          className={activeTab === 'pr' ? 'active' : ''}
          onClick={() => setActiveTab('pr')}
        >
          GitHub PR
        </button>
        <button
          className={activeTab === 'diff' ? 'active' : ''}
          onClick={() => setActiveTab('diff')}
        >
          Raw Diff
        </button>
      </div>

      <div className="forms">
        {activeTab === 'pr' ? (
          <PRForm onSubmit={handlePRSubmit} loading={loading} />
        ) : (
          <DiffForm onSubmit={handleDiffSubmit} loading={loading} />
        )}
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {reviews.length > 0 && (
        <div className="results">
          <div className="results-header">
            <h2>Review Results ({reviews.length})</h2>
            <button onClick={copyToClipboard} className="copy-btn">
              Copy JSON
            </button>
          </div>

          <div className="reviews-list">
            {reviews.map((review, index) => (
              <ReviewCard key={index} review={review} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
