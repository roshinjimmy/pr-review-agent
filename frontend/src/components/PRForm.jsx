import { useState } from 'react'

function PRForm({ onSubmit, loading }) {
  const [repo, setRepo] = useState('')
  const [prNumber, setPrNumber] = useState('')
  const [githubToken, setGithubToken] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      repo,
      pr_number: parseInt(prNumber),
      github_token: githubToken
    })
  }

  return (
    <div className="form-container">
      <h2>Review GitHub PR</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="repo">Repository (owner/repo)</label>
          <input
            type="text"
            id="repo"
            placeholder="octocat/hello-world"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="prNumber">PR Number</label>
          <input
            type="number"
            id="prNumber"
            placeholder="123"
            value={prNumber}
            onChange={(e) => setPrNumber(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="githubToken">GitHub Token</label>
          <input
            type="password"
            id="githubToken"
            placeholder="ghp_..."
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            required
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Review PR'}
        </button>
      </form>
    </div>
  )
}

export default PRForm
