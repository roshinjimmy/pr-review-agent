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


def build_review_crew() -> Crew:
    """Create a Crew with all review agents wired together."""

    readability_task = Task(
        description=(
            "Analyze the provided structured diff for readability issues, "
            "including naming, comments, formatting, and clarity. "
            "Return findings as JSON array with file, line, severity, issue, recommendation."
        ),
        agent=readability_agent,
        expected_output="A JSON array of readability findings.",
    )

    logic_task = Task(
        description=(
            "Review the structured diff for logic errors, missing edge cases, "
            "and potential bugs. "
            "Return findings as JSON array with file, line, severity, issue, recommendation."
        ),
        agent=logic_agent,
        expected_output="A JSON array of logic and bug findings.",
    )

    performance_task = Task(
        description=(
            "Inspect the structured diff for performance issues such as "
            "inefficient loops, redundant work, or unnecessary allocations. "
            "Return findings as JSON array with file, line, severity, issue, recommendation."
        ),
        agent=performance_agent,
        expected_output="A JSON array of performance findings.",
    )

    security_task = Task(
        description=(
            "Scan the structured diff for security issues such as unsafe "
            "patterns, insecure APIs, injection risks, and hardcoded secrets. "
            "Return findings as JSON array with file, line, severity, issue, recommendation."
        ),
        agent=security_agent,
        expected_output="A JSON array of security findings.",
    )

    consolidation_task = Task(
        description=(
            "Combine and deduplicate findings from readability, logic, "
            "performance, and security into a single, clean JSON array of review comments. "
            "Each comment must have: file, line, severity, issue, recommendation, source."
        ),
        agent=consolidation_agent,
        expected_output=(
            "A JSON object with a 'comments' array containing consolidated review comments."
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

    crew = build_review_crew()
    
    # Pass the structured diff to the crew
    result = crew.kickoff(inputs={"structured_diff": structured_diff})
    
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
        comments = []
    
    return {"comments": comments}
