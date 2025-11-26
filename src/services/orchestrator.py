from __future__ import annotations

from typing import Any, Dict, List

from crewai import Crew, Process, Task

from src.agents.agents import (
    consolidation_agent,
    logic_agent,
    performance_agent,
    readability_agent,
    security_agent,
)
from src.utils.logger import setup_logger, log_with_context

logger = setup_logger(__name__)


def build_review_crew() -> Crew:
    """Create a Crew with all review agents wired together."""

    readability_task = Task(
        description=(
            "Review this code for readability issues:\n\n{diff_context}\n\n"
            "Analyze ONLY the lines marked with (+) for: poor variable/function naming, "
            "missing comments, inconsistent formatting, unclear logic flow. "
            "For each issue found, return a JSON object with: file (string), line (number), "
            "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
            "issue (brief description), recommendation (how to fix), source (must be 'readability'). "
            "Return ONLY a JSON array of findings, nothing else."
        ),
        agent=readability_agent,
        expected_output="A JSON array of readability findings with source='readability'.",
    )

    logic_task = Task(
        description=(
            "Review this code for logic errors and bugs:\n\n{diff_context}\n\n"
            "Analyze ONLY the lines marked with (+) for: incorrect conditions, missing null/undefined checks, "
            "off-by-one errors, incorrect return values, missing error handling, unreachable code. "
            "For each issue found, return a JSON object with: file (string), line (number), "
            "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
            "issue (brief description), recommendation (how to fix), source (must be 'logic'). "
            "Return ONLY a JSON array of findings, nothing else."
        ),
        agent=logic_agent,
        expected_output="A JSON array of logic and bug findings with source='logic'.",
    )

    performance_task = Task(
        description=(
            "Review this code for performance issues:\n\n{diff_context}\n\n"
            "Analyze ONLY the lines marked with (+) for: nested loops with O(n²) or worse complexity, "
            "redundant operations inside loops, unnecessary memory allocations, inefficient algorithms, "
            "repeated expensive operations that should be cached, N+1 query patterns. "
            "For each issue found, return a JSON object with: file (string), line (number), "
            "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
            "issue (brief description), recommendation (how to fix), source (must be 'performance'). "
            "Return ONLY a JSON array of findings, nothing else."
        ),
        agent=performance_agent,
        expected_output="A JSON array of performance findings with source='performance'.",
    )

    security_task = Task(
        description=(
            "Review this code for security vulnerabilities:\n\n{diff_context}\n\n"
            "Analyze ONLY the lines marked with (+) for: SQL/command injection risks, XSS vulnerabilities, "
            "hardcoded secrets/credentials, insecure APIs, missing input validation, unsafe deserialization, "
            "path traversal, SSRF, insecure random number generation. "
            "For each issue found, return a JSON object with: file (string), line (number), "
            "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
            "issue (brief description), recommendation (how to fix), source (must be 'security'). "
            "Return ONLY a JSON array of findings, nothing else."
        ),
        agent=security_agent,
        expected_output="A JSON array of security findings with source='security'.",
    )

    consolidation_task = Task(
        description=(
            "Combine and deduplicate findings from readability, logic, "
            "performance, and security into a single, clean JSON array of review comments. "
            "Each comment must have: file, line, severity, issue, recommendation, and source. "
            "Severity must be one of: 'critical', 'error', 'warning', 'high', 'moderate', 'medium', 'low', 'info'. "
            "IMPORTANT: Keep the source field as a single string value from the original agent "
            "(e.g., 'readability', 'logic', 'performance', or 'security'). "
            "Do NOT combine multiple sources into one field. If the same issue appears from multiple agents, "
            "pick the most relevant source or create separate comments."
        ),
        agent=consolidation_agent,
        expected_output=(
            "A JSON object with a 'comments' array where each comment has a single source value."
        ),
    )

    crew = Crew(
        agents=[
            readability_agent,
            logic_agent,
            performance_agent,
            security_agent,
            consolidation_agent,
        ],
        tasks=[
            readability_task,
            logic_task,
            performance_task,
            security_task,
            consolidation_task,
        ],
        process=Process.sequential,
    )

    return crew


def run_review_pipeline(structured_diff: Dict[str, Any]) -> Dict[str, Any]:
    """Run the CrewAI review pipeline on a structured diff.
    """
    import json
    import re

    logger.info("Starting review pipeline")
    
    # Format the diff data as a readable string for the LLM
    diff_context = "Code changes to review:\n\n"
    for file_data in structured_diff.get("files", []):
        diff_context += f"File: {file_data['file']}\n"
        diff_context += "Changes:\n"
        for change in file_data.get("changes", []):
            if change["type"] == "addition":
                diff_context += f"  Line {change['line']} (+): {change['content']}\n"
            elif change["type"] == "deletion":
                diff_context += f"  Line {change['line']} (-): {change['content']}\n"
        diff_context += "\n"

    logger.info("Running ReadabilityAgent")
    logger.info("Running LogicAgent")
    logger.info("Running PerformanceAgent")
    logger.info("Running SecurityAgent")
    
    crew = build_review_crew()
    
    # Pass both structured and formatted diff to the crew
    result = crew.kickoff(inputs={
        "structured_diff": structured_diff,
        "diff_context": diff_context
    })
    
    # Parse the crew output
    result_str = str(result)

    json_match = re.search(r"```json\s*\n(.*?)\n```", result_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = result_str

    try:
        parsed = json.loads(json_str)
        comments = parsed.get("comments", [])
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM output as JSON")
        comments = []
    
    logger.info("Running ConsolidationAgent")
    
    log_with_context(
        logger, "info", "Review pipeline completed",
        total_issues=len(comments),
        critical=len([c for c in comments if c.get("severity") == "critical"]),
        error=len([c for c in comments if c.get("severity") == "error"]),
        warning=len([c for c in comments if c.get("severity") == "warning"]),
        info=len([c for c in comments if c.get("severity") in ["info", "low", "medium", "moderate", "high"]])
    )
    
    return {"comments": comments}
