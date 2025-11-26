import { useState } from 'react'

function DiffForm({ onSubmit, loading }) {
  const [diff, setDiff] = useState('')

  const exampleDiff = `diff --git a/app.py b/app.py
index abc..def 100644
--- a/app.py
+++ b/app.py
@@ -10,3 +10,5 @@ def process():
     result = []
+    for i in range(len(items)):
+        result.append(items[i].upper())
     return result`

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ diff })
  }

  const loadExample = () => {
    setDiff(exampleDiff)
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pastedText = e.clipboardData.getData('text')
    // Convert escaped newlines to actual newlines
    const convertedText = pastedText.replace(/\\n/g, '\n')
    setDiff(convertedText)
  }

  return (
    <div className="form-container">
      <h2>Review Raw Diff</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="diff">
            Paste Unified Diff
            <button 
              type="button" 
              className="load-example-btn" 
              onClick={loadExample}
              disabled={loading}
            >
              Load Example
            </button>
          </label>
          <textarea
            id="diff"
            placeholder="Paste your git diff output here..."
            value={diff}
            onChange={(e) => setDiff(e.target.value)}
            onPaste={handlePaste}
            rows="15"
            required
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Review Diff'}
        </button>
      </form>
    </div>
  )
}

export default DiffForm
