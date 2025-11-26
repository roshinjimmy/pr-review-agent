"""Unit tests for orchestrator."""

import pytest
from unittest.mock import patch, MagicMock
from src.services.orchestrator import run_review_pipeline


def test_run_review_pipeline_basic():
    """Test basic orchestrator execution."""
    structured_diff = {
        "files": [
            {
                "file": "test.py",
                "changes": [
                    {"type": "addition", "line": 10, "content": "    x = 1"}
                ]
            }
        ]
    }
    
    # Mock CrewAI's Crew.kickoff to return a JSON response
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: '''```json
{
    "comments": [
        {
            "file": "test.py",
            "line": 10,
            "severity": "low",
            "issue": "Variable name 'x' is not descriptive",
            "recommendation": "Use a more descriptive name",
            "source": "readability"
        }
    ]
}
```'''
    
    with patch("src.services.orchestrator.build_review_crew") as mock_build:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_build.return_value = mock_crew
        
        result = run_review_pipeline(structured_diff)
        
        assert "comments" in result
        assert len(result["comments"]) == 1
        assert result["comments"][0]["file"] == "test.py"
        assert result["comments"][0]["severity"] == "low"


def test_run_review_pipeline_empty_response():
    """Test orchestrator handling empty LLM response."""
    structured_diff = {
        "files": [
            {
                "file": "empty.py",
                "changes": []
            }
        ]
    }
    
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: '{"comments": []}'
    
    with patch("src.services.orchestrator.build_review_crew") as mock_build:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_build.return_value = mock_crew
        
        result = run_review_pipeline(structured_diff)
        
        assert "comments" in result
        assert len(result["comments"]) == 0


def test_run_review_pipeline_invalid_json():
    """Test orchestrator handling invalid JSON from LLM."""
    structured_diff = {
        "files": [
            {
                "file": "test.py",
                "changes": [
                    {"type": "addition", "line": 5, "content": "code"}
                ]
            }
        ]
    }
    
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "This is not valid JSON"
    
    with patch("src.services.orchestrator.build_review_crew") as mock_build:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_build.return_value = mock_crew
        
        result = run_review_pipeline(structured_diff)
        
        # Should return empty comments on parse failure
        assert "comments" in result
        assert len(result["comments"]) == 0


def test_run_review_pipeline_multiple_issues():
    """Test orchestrator with multiple review comments."""
    structured_diff = {
        "files": [
            {
                "file": "app.py",
                "changes": [
                    {"type": "addition", "line": 15, "content": "    password = '123'"},
                    {"type": "addition", "line": 20, "content": "    for i in range(n):"}
                ]
            }
        ]
    }
    
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: '''```json
{
    "comments": [
        {
            "file": "app.py",
            "line": 15,
            "severity": "critical",
            "issue": "Hardcoded password",
            "recommendation": "Use environment variables",
            "source": "security"
        },
        {
            "file": "app.py",
            "line": 20,
            "severity": "low",
            "issue": "Variable name 'n' is unclear",
            "recommendation": "Use descriptive name like 'item_count'",
            "source": "readability"
        }
    ]
}
```'''
    
    with patch("src.services.orchestrator.build_review_crew") as mock_build:
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_result
        mock_build.return_value = mock_crew
        
        result = run_review_pipeline(structured_diff)
        
        assert len(result["comments"]) == 2
        assert result["comments"][0]["severity"] == "critical"
        assert result["comments"][0]["source"] == "security"
        assert result["comments"][1]["severity"] == "low"
        assert result["comments"][1]["source"] == "readability"
