"""GitHub API integration for fetching PR diffs."""

import httpx
from typing import Optional


class GitHubAPIError(Exception):
    """Exception raised when GitHub API calls fail."""
    pass


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
            return response.text
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise GitHubAPIError(
                    f"Pull request not found: {repo_owner}/{repo_name}#{pr_number}"
                )
            elif e.response.status_code == 401:
                raise GitHubAPIError("Invalid or expired GitHub token")
            elif e.response.status_code == 403:
                raise GitHubAPIError("Access forbidden - check token permissions")
            else:
                raise GitHubAPIError(
                    f"GitHub API error: {e.response.status_code} - {e.response.text}"
                )
                
        except httpx.TimeoutException:
            raise GitHubAPIError("Request to GitHub API timed out")
            
        except httpx.RequestError as e:
            raise GitHubAPIError(f"Failed to connect to GitHub API: {str(e)}")
