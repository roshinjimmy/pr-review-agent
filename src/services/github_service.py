"""GitHub API integration for fetching PR diffs."""

import httpx
from typing import Optional


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message: str, error_type: str = "GitHubAPIError", details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details


class PRNotFoundError(GitHubAPIError):
    """PR or repository not found."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "PRNotFoundError", details)


class InvalidTokenError(GitHubAPIError):
    """Invalid or expired GitHub token."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "InvalidTokenError", details)


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "RateLimitError", details)


class EmptyPRError(GitHubAPIError):
    """PR has no file changes."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "EmptyPRError", details)


class BinaryDiffError(GitHubAPIError):
    """PR contains binary files that cannot be reviewed."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "BinaryDiffError", details)


class NetworkError(GitHubAPIError):
    """Network connectivity issue."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "NetworkError", details)


async def fetch_pr_diff(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    github_token: str
) -> str:
    """
    Fetch the unified diff for a GitHub Pull Request.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3.diff",  # Request diff format
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            diff_text = response.text
            
            # Check for empty PR
            if not diff_text or diff_text.strip() == "":
                raise EmptyPRError(
                    f"Pull request #{pr_number} has no file changes",
                    details=f"GET {url} returned empty diff"
                )
            
            # Check for binary files indicator
            if "Binary files" in diff_text or "GIT binary patch" in diff_text:
                raise BinaryDiffError(
                    "Pull request contains binary files that cannot be reviewed as text",
                    details="Detected binary file markers in diff output"
                )
            
            return diff_text
            
        except httpx.HTTPStatusError as e:
            details = f"GET {url} returned {e.response.status_code}"
            
            if e.response.status_code == 404:
                raise PRNotFoundError(
                    f"Pull request not found: {repo_owner}/{repo_name}#{pr_number}",
                    details=f"{details}. Repository or PR may not exist, or you lack access."
                )
            elif e.response.status_code == 401:
                raise InvalidTokenError(
                    "Invalid or expired GitHub token",
                    details=f"{details}. Check your personal access token."
                )
            elif e.response.status_code == 403:
                # Check if it's rate limiting
                if "rate limit" in e.response.text.lower():
                    raise RateLimitError(
                        "GitHub API rate limit exceeded",
                        details=f"{details}. Wait before making more requests or use authenticated token."
                    )
                else:
                    raise InvalidTokenError(
                        "Access forbidden - insufficient token permissions",
                        details=f"{details}. Token may need 'repo' or 'public_repo' scope."
                    )
            else:
                raise GitHubAPIError(
                    f"GitHub API request failed with status {e.response.status_code}",
                    details=f"{details}: {e.response.text[:200]}"
                )
                
        except httpx.TimeoutException:
            raise NetworkError(
                "Request to GitHub API timed out",
                details=f"Timeout after 30 seconds connecting to {url}"
            )
            
        except httpx.RequestError as e:
            raise NetworkError(
                "Failed to connect to GitHub API",
                details=f"Network error: {str(e)}"
            )
