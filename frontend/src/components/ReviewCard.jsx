function ReviewCard({ review }) {
  const getSeverityClass = (severity) => {
    const severityLower = severity?.toLowerCase() || ''
    if (severityLower.includes('error') || severityLower.includes('critical')) {
      return 'severity-error'
    }
    if (severityLower.includes('warning') || severityLower.includes('warn') || severityLower.includes('high')) {
      return 'severity-warning'
    }
    return 'severity-info'
  }

  return (
    <div className="review-card">
      <div className="review-header">
        <div className="review-file">
          <strong>{review.file}</strong>
          {review.line && <span className="line-number">Line {review.line}</span>}
        </div>
        <div className="review-meta">
          <span className={`severity ${getSeverityClass(review.severity)}`}>
            {review.severity}
          </span>
          {review.source && <span className="agent">{review.source}</span>}
        </div>
      </div>

      <div className="review-content">
        <div className="issue">
          <h4>Issue:</h4>
          <p>{review.issue}</p>
        </div>

        {review.recommendation && (
          <div className="suggestion">
            <h4>Recommendation:</h4>
            <p>{review.recommendation}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReviewCard
