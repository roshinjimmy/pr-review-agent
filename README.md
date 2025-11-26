# PR Review Agent

A fully automated Pull Request review system powered by AI multi-agents with a modern React frontend. Analyze code changes for readability, logic errors, performance issues, and security vulnerabilities using CrewAI and LLMs.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                    │
│              (GitHub PR Form + Raw Diff Form)                │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                        FastAPI Server                        │
│                     (Health + 2 Endpoints)                   │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
        ┌───────▼────────┐          ┌──────────▼─────────┐
        │  /review/diff  │          │   /review/pr       │
        │  (Raw Diff)    │          │  (GitHub PR)       │
        └───────┬────────┘          └──────────┬─────────┘
                │                              │
                │                    ┌─────────▼──────────┐
                │                    │  GitHub API Client │
                │                    │  (Fetch PR Diff)   │
                │                    └─────────┬──────────┘
                │                              │
                └──────────────┬───────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Diff Parser        │
                    │  (Unified Format)    │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Parallel Execution   │
                    │ (ThreadPoolExecutor) │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐───────────────────┐
        │                      │                      │                   │
   ┌────▼──────┐  ┌────────────▼───────┐  ┌───────────▼──────┐  ┌─────────▼─────┐
   │Readability│  │     Logic          │  │  Performance     │  │   Security    │
   │  Agent    │  │     Agent          │  │    Agent         │  │    Agent      │
   └────┬──────┘  └────────────┬───────┘  └───────────┬──────┘  └────────┬──────┘
        │                      │                      │                  │
        └──────────────────────┼──────────────────────┴──────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Programmatic       │
                    │   Deduplication      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Structured JSON     │
                    │   Response           │
                    └──────────────────────┘
```

## Features

### Modern Web Interface
- **Clean React UI** - Minimal, developer-friendly interface built with React + Vite
- **Dual Input Modes** - Tab-based interface for GitHub PR or raw diff input
- **Real-time Results** - Display review comments with color-coded severity levels
- **Smart Diff Handling** - Automatic conversion of escaped newlines in pasted diffs
- **Example Loader** - One-click example diff for quick testing
- **JSON Export** - Copy results to clipboard as JSON

### Multi-Agent Review System (Parallel Execution)
- **Readability Agent**: Analyzes naming, comments, formatting, and code clarity
- **Logic Agent**: Detects bugs, edge cases, and logical errors
- **Performance Agent**: Identifies inefficient algorithms, nested loops, and bottlenecks
- **Security Agent**: Scans for vulnerabilities, injection risks, and hardcoded secrets
- **Programmatic Deduplication**: Fast, deterministic merging of findings

**Architecture Highlights:**
- All 4 review agents run in parallel using ThreadPoolExecutor
- Each agent operates independently with `allow_delegation=False`
- Consolidation replaced with efficient programmatic deduplication
- ~70% faster processing time with zero quality loss

### Two Review Modes
1. **Direct Diff Review** (`/review/diff`) - Analyze raw git diff text
2. **GitHub PR Review** (`/review/pr`) - Fetch and review PRs directly from GitHub

### Production-Ready Features
- Structured JSON logging for monitoring
- Comprehensive error handling with typed exceptions
- Pydantic schema validation
- Health endpoint with uptime tracking
- Rate limit handling
- Binary file detection
- Empty PR validation
- CORS enabled for frontend integration

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- OpenRouter API key (for LLM access)
- GitHub Personal Access Token (for `/review/pr` endpoint)

## Installation

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/roshinjimmy/pr-review-agent.git
cd pr-review-agent/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "OPENROUTER_API_KEY=your_key_here" > src/.env

# Run the server
uvicorn src.main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create .env file (optional - defaults to localhost:8000)
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Quick Start (Both Services)

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn src.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## API Endpoints

### 1. Health Check

```bash
GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "uptime_seconds": 123.45,
  "version": "0.1.0"
}
```

---

### 2. Review Raw Diff

```bash
POST http://localhost:8000/review/diff
Content-Type: application/json
```

**Request Body:**
```json
{
  "diff": "diff --git a/app.py b/app.py\nindex abc..def 100644\n--- a/app.py\n+++ b/app.py\n@@ -10,3 +10,5 @@ def process():\n     result = []\n+    for i in range(len(items)):\n+        result.append(items[i].upper())\n     return result\n"
}
```

**Response:**
```json
{
  "comments": [
    {
      "file": "app.py",
      "line": 12,
      "severity": "medium",
      "issue": "The list 'result' is unnecessarily created; list comprehension can be used for better performance.",
      "recommendation": "Use a list comprehension: 'result = [item.upper() for item in items]' which is more concise and efficient.",
      "source": "performance"
    },
    {
      "file": "app.py",
      "line": 11,
      "severity": "error",
      "issue": "Missing null/undefined checks for 'items'.",
      "recommendation": "Before iterating over 'items', ensure that it is not None or handle the case if it is.",
      "source": "logic"
    }
  ]
}
```

---

### 3. Review GitHub PR

```bash
POST http://localhost:8000/review/pr
Content-Type: application/json
```

**Request Body:**
```json
{
  "repo_owner": "facebook",
  "repo_name": "react",
  "pr_number": 12345,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

**Response:**
```json
{
  "comments": [
    {
      "file": "src/component.js",
      "line": 45,
      "severity": "critical",
      "issue": "Potential XSS vulnerability - user input not sanitized",
      "recommendation": "Use DOMPurify or escape HTML before rendering",
      "source": "security"
    },
    {
      "file": "src/utils.js",
      "line": 23,
      "severity": "warning",
      "issue": "Nested loop causing O(n²) complexity",
      "recommendation": "Use a Set or Map for O(n) lookup instead",
      "source": "performance"
    }
  ]
}
```

## Multi-Agent Workflow

### Parallel Processing (Optimized)

```
1. Input (Raw Diff or GitHub PR)
   ↓
2. Parse Unified Diff → Structured JSON
   ↓
3. Parallel Execution (4 agents run simultaneously)
   ├─ Readability Agent → Analyzes code style
   ├─ Logic Agent → Detects bugs and edge cases
   ├─ Performance Agent → Identifies bottlenecks
   └─ Security Agent → Scans for vulnerabilities
   ↓
4. Programmatic Deduplication → Merges findings
   ↓
5. Output (Structured JSON with severity levels)
```

**Performance Benefits:**
- 4 agents execute in parallel using ThreadPoolExecutor
- ~70% faster than sequential execution
- Reduced from ~60s to ~15-20s per review
- No quality degradation - same analysis depth

### Severity Levels

- **critical** - Security vulnerabilities, data loss risks, crashes
- **error** - Logic errors, bugs that break functionality
- **warning** - Potential issues, code smells
- **high/moderate/medium** - Various levels of improvements needed
- **low** - Minor suggestions, style preferences
- **info** - Informational, FYI items

## Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_diff_parser.py -v
```

**Test Coverage:**
- 14 unit tests (100% pass rate)
- Diff parser (5 tests)
- GitHub service (5 tests)
- Orchestrator (4 tests)

## Sample Output

### Test Case: Nested Loops (Performance Issue)

**Input Diff:**
```diff
diff --git a/app/processor.py b/app/processor.py
@@ -10,6 +10,9 @@ def process_items(items):
     result = []
+    for i in range(len(items)):
+        for j in range(len(items)):
+            result.append(items[i] + items[j])
     return result
```

**AI Review Output:**
```json
{
  "comments": [
    {
      "file": "app/processor.py",
      "line": 12,
      "severity": "critical",
      "issue": "Unnecessarily nested loop causing high computational cost",
      "recommendation": "Refactor to prevent nesting by using itertools.combinations or a different algorithm",
      "source": "performance"
    },
    {
      "file": "app/processor.py",
      "line": 13,
      "severity": "low",
      "issue": "Inefficient O(n²) complexity",
      "recommendation": "Consider using itertools.combinations or a single loop with a mathematical formula",
      "source": "performance"
    },
    {
      "file": "app/processor.py",
      "line": 11,
      "severity": "critical",
      "issue": "Potential for IndexError",
      "recommendation": "Check that 'items' is not null/undefined and has at least two elements",
      "source": "logic"
    }
  ]
}
```

## Postman Examples

### Example 1: Successful GitHub PR Review

**Request:**
```json
{
  "repo_owner": "paritomarrr",
  "repo_name": "gharsetu-frontend",
  "pr_number": 3,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

**Console Logs (Structured JSON):**
```json
{"timestamp": "2025-11-26T12:53:15.629474Z", "level": "INFO", "logger": "src.main", "message": "Received PR review request", "endpoint": "/review/pr", "repo": "paritomarrr/gharsetu-frontend", "pr_number": 3}

{"timestamp": "2025-11-26T12:53:16.252762Z", "level": "INFO", "logger": "src.services.github_service", "message": "Successfully fetched PR diff", "repo": "paritomarrr/gharsetu-frontend", "pr_number": 3, "status_code": 200, "diff_size_bytes": 17046}

{"timestamp": "2025-11-26T12:53:16.253682Z", "level": "INFO", "logger": "src.utils.diff_parser", "message": "Diff parsing completed", "files_parsed": 8, "total_changes": 394, "additions": 223, "deletions": 28}

{"timestamp": "2025-11-26T12:54:13.919537Z", "level": "INFO", "logger": "src.services.orchestrator", "message": "Review pipeline completed", "total_issues": 10, "critical": 1, "error": 0, "warning": 2, "info": 7}
```

---

### Example 2: Error Handling - PR Not Found

**Request:**
```json
{
  "repo_owner": "nonexistent",
  "repo_name": "fake-repo",
  "pr_number": 999,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

**Response (404):**
```json
{
  "error": {
    "type": "PRNotFoundError",
    "message": "Pull request not found: nonexistent/fake-repo#999",
    "details": "GET https://api.github.com/repos/nonexistent/fake-repo/pulls/999 returned 404. Repository or PR may not exist, or you lack access."
  }
}
```

---

### Example 3: Nested Loop Detection

**Request to `/review/diff`:**
```json
{
  "diff": "diff --git a/app/processor.py b/app/processor.py\nindex abc123..def456 100644\n--- a/app/processor.py\n+++ b/app/processor.py\n@@ -10,6 +10,9 @@ def process_items(items):\n     result = []\n+    for i in range(len(items)):\n+        for j in range(len(items)):\n+            result.append(items[i] + items[j])\n     return result\n"
}
```

**Response (200 OK):**
```json
{
  "comments": [
    {
      "file": "app/processor.py",
      "line": 11,
      "severity": "critical",
      "issue": "Potential for IndexError",
      "recommendation": "Before referencing items[i] and items[j], check that 'items' is not null/undefined and has at least two elements.",
      "source": "logic"
    },
    {
      "file": "app/processor.py",
      "line": 12,
      "severity": "critical",
      "issue": "Unnecessarily nested loop causing high computational cost",
      "recommendation": "Refactor to prevent nesting by using a different algorithm or data structure that can optimize the combination of items.",
      "source": "performance"
    },
    {
      "file": "app/processor.py",
      "line": 13,
      "severity": "low",
      "issue": "Inefficient O(n^2) complexity",
      "recommendation": "Consider using itertools.combinations or a single loop with a mathematical formula to generate pairs of items instead of nested loops.",
      "source": "performance"
    }
  ]
}
```

## Error Handling

### Structured Error Responses

All errors follow this format:

```json
{
  "error": {
    "type": "ErrorTypeName",
    "message": "Human-readable message",
    "details": "Technical details for debugging"
  }
}
```

### Error Types & HTTP Status Codes

| Error Type | Status Code | Description |
|------------|-------------|-------------|
| `PRNotFoundError` | 404 | PR or repository not found |
| `InvalidTokenError` | 401 | Invalid/expired GitHub token |
| `RateLimitError` | 429 | GitHub API rate limit exceeded |
| `EmptyPRError` | 422 | PR has no file changes |
| `BinaryDiffError` | 422 | PR contains binary files |
| `NetworkError` | 503 | Connection timeout or network issue |
| `InternalError` | 500 | Unexpected server error |

## Project Structure

```
pr-review-agent/
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   └── agents.py              # CrewAI agent definitions
│   │   ├── models/
│   │   │   ├── diff.py                # Input request models
│   │   │   ├── review.py              # Output response models
│   │   │   └── errors.py              # Error response models
│   │   ├── services/
│   │   │   ├── github_service.py      # GitHub API integration
│   │   │   └── orchestrator.py        # Multi-agent workflow
│   │   ├── utils/
│   │   │   ├── diff_parser.py         # Unified diff parser
│   │   │   └── logger.py              # JSON logging utility
│   │   ├── main.py                    # FastAPI application
│   │   └── .env                       # API keys (not committed)
│   ├── tests/
│   │   ├── test_diff_parser.py        # Parser unit tests
│   │   ├── test_github_service.py     # GitHub service tests
│   │   ├── test_orchestrator.py       # Orchestrator tests
│   │   └── conftest.py                # Pytest configuration
│   ├── requirements.txt               # Production dependencies
│   └── pyproject.toml                 # Pytest configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PRForm.jsx             # GitHub PR input form
│   │   │   ├── DiffForm.jsx           # Raw diff input form
│   │   │   └── ReviewCard.jsx         # Review result card
│   │   ├── App.jsx                    # Main application
│   │   ├── App.css                    # Application styles
│   │   ├── main.jsx                   # React entry point
│   │   └── index.css                  # Global styles
│   ├── public/                        # Static assets
│   ├── .env                           # Environment config (not committed)
│   ├── .env.example                   # Example config
│   ├── package.json                   # Dependencies
│   ├── vite.config.js                 # Vite configuration
│   └── index.html                     # HTML template
│
└── README.md
```

## Key Technologies

### Backend
- **FastAPI** - Modern async web framework
- **CrewAI** - Multi-agent orchestration
- **OpenRouter** - LLM API gateway (GPT-4o-mini)
- **Pydantic** - Data validation
- **httpx** - Async HTTP client
- **pytest** - Testing framework

### Frontend
- **React 19** - UI library
- **Vite** - Fast build tool and dev server
- **Vanilla CSS** - Clean, custom styling (no frameworks)


## Performance Metrics

### Optimized Performance (Latest)
From actual production runs:
- GitHub API latency: ~600ms
- Diff parsing: <1ms
- Parallel agent execution: ~12-15 seconds (4 agents simultaneously)
- Deduplication: <1ms
- **Total request time: ~15-20 seconds** (depends on diff size)

### Performance Improvements
- **Before optimization**: 60 seconds (5 agents sequential)
- **After optimization**: 15-20 seconds (4 agents parallel)
- **Speed improvement**: ~70% faster ⚡
- **Quality maintained**: Zero degradation in review accuracy

### Optimization Techniques Applied
1. Parallel execution using ThreadPoolExecutor (4 concurrent agents)
2. Programmatic deduplication (replaced consolidation agent LLM call)
3. Agent configuration optimization (`allow_delegation=False`, `verbose=False`)
4. Removed redundant CrewAI overhead


## Future Enhancements
- [ ] WebSocket support for real-time streaming updates
- [ ] Caching layer for repeated PR reviews
- [ ] Support for more LLM providers (Anthropic, Groq)
- [ ] GitHub webhook integration for automatic reviews
- [ ] Custom rule configuration per repository
- [ ] Integration with GitHub PR comments API
- [ ] Smart file filtering (skip generated files, configs)

## License

MIT License
