from __future__ import annotations

from typing import Any, Dict

from crewai import Crew, Process, Task

from src.agents.agents import (
    consolidation_agent,
    logic_agent,
    performance_agent,
    readability_agent,
    security_agent,
)


def build_review_crew() -> Crew:
    """Create a Crew with all review agents wired together.
    """

    readability_task = Task(
        description=(
            "Analyze the provided structured diff for readability issues, "
            "including naming, comments, formatting, and clarity."
        ),
        agent=readability_agent,
        expected_output="A JSON-style list of readability findings.",
    )

    logic_task = Task(
        description=(
            "Review the structured diff for logic errors, missing edge cases, "
            "and potential bugs."
        ),
        agent=logic_agent,
        expected_output="A JSON-style list of logic and bug findings.",
    )

    performance_task = Task(
        description=(
            "Inspect the structured diff for performance issues such as "
            "inefficient loops, redundant work, or unnecessary allocations."
        ),
        agent=performance_agent,
        expected_output="A JSON-style list of performance findings.",
    )

    security_task = Task(
        description=(
            "Scan the structured diff for security issues such as unsafe "
            "patterns, insecure APIs, injection risks, and hardcoded secrets."
        ),
        agent=security_agent,
        expected_output="A JSON-style list of security findings.",
    )

    consolidation_task = Task(
        description=(
            "Combine and deduplicate findings from readability, logic, "
            "performance, and security into a single, clean JSON review "
            "response suitable for GitHub."
        ),
        agent=consolidation_agent,
        expected_output=(
            "A JSON object with an array of consolidated review comments, "
            "each having file, line, severity, issue description, "
            "recommendation, and agent source."
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
    """Run the review pipeline on a structured diff.
    """

    crew = build_review_crew()

    result = crew.kickoff(inputs={"structured_diff": structured_diff})
    
    return {"raw_result": str(result)}
