"""Unit tests for GitHub API service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.github_service import (
    fetch_pr_diff,
    PRNotFoundError,
    InvalidTokenError,
    RateLimitError,
    EmptyPRError,
    BinaryDiffError,
    NetworkError
)
import httpx


@pytest.mark.asyncio
async def test_fetch_pr_diff_success():
    """Test successful PR diff fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,2 @@
 original
+new line
"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await fetch_pr_diff("owner", "repo", 123, "fake_token")
        
        assert "diff --git" in result
        assert "new line" in result


@pytest.mark.asyncio
async def test_fetch_pr_diff_not_found():
    """Test PR not found error."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response))
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        with pytest.raises(PRNotFoundError) as exc_info:
            await fetch_pr_diff("owner", "repo", 999, "fake_token")
        
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_fetch_pr_diff_invalid_token():
    """Test invalid token error."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock(side_effect=httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response))
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await fetch_pr_diff("owner", "repo", 123, "invalid_token")
        
        assert "token" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_fetch_pr_diff_empty():
    """Test empty PR detection."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(EmptyPRError):
            await fetch_pr_diff("owner", "repo", 123, "fake_token")


@pytest.mark.asyncio
async def test_fetch_pr_diff_binary_files():
    """Test binary files detection."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(BinaryDiffError):
            await fetch_pr_diff("owner", "repo", 123, "fake_token")
