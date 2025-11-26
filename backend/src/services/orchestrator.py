from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from crewai import Crew, Process, Task

from src.agents.agents import (
    logic_agent,
    performance_agent,
    readability_agent,
    security_agent,
)
from src.utils.logger import setup_logger, log_with_context

logger = setup_logger(__name__)

# Task descriptions for each review agent
READABILITY_DESC = (
    "Review this code for readability issues:\n\n{diff_context}\n\n"
    "Analyze ONLY the lines marked with (+) for: poor variable/function naming, "
    "missing comments, inconsistent formatting, unclear logic flow. "
    "For each issue found, return a JSON object with: file (string), line (number), "
    "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
    "issue (brief description), recommendation (how to fix), source (must be 'readability'). "
    "Return ONLY a JSON array of findings, nothing else."
)

LOGIC_DESC = (
    "Review this code for logic errors and bugs:\n\n{diff_context}\n\n"
    "Analyze ONLY the lines marked with (+) for: incorrect conditions, missing null/undefined checks, "
    "off-by-one errors, incorrect return values, missing error handling, unreachable code. "
    "For each issue found, return a JSON object with: file (string), line (number), "
    "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
    "issue (brief description), recommendation (how to fix), source (must be 'logic'). "
    "Return ONLY a JSON array of findings, nothing else."
)

PERFORMANCE_DESC = (
    "Review this code for performance issues:\n\n{diff_context}\n\n"
    "Analyze ONLY the lines marked with (+) for: nested loops with O(n²) or worse complexity, "
    "redundant operations inside loops, unnecessary memory allocations, inefficient algorithms, "
    "repeated expensive operations that should be cached, N+1 query patterns. "
    "For each issue found, return a JSON object with: file (string), line (number), "
    "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
    "issue (brief description), recommendation (how to fix), source (must be 'performance'). "
    "Return ONLY a JSON array of findings, nothing else."
)

SECURITY_DESC = (
    "Review this code for security vulnerabilities:\n\n{diff_context}\n\n"
    "Analyze ONLY the lines marked with (+) for: SQL/command injection risks, XSS vulnerabilities, "
    "hardcoded secrets/credentials, insecure APIs, missing input validation, unsafe deserialization, "
    "path traversal, SSRF, insecure random number generation. "
    "For each issue found, return a JSON object with: file (string), line (number), "
    "severity (one of: critical, error, warning, high, moderate, medium, low, info), "
    "issue (brief description), recommendation (how to fix), source (must be 'security'). "
    "Return ONLY a JSON array of findings, nothing else."
)


def _run_single_agent_task(agent, task_description: str, diff_context: str, agent_name: str) -> str:
    """Run a single agent task and return the result."""
    import json
    
    logger.info(f"Running {agent_name}")
    
    # Create a minimal crew with just one agent and task
    task = Task(
        description=task_description.format(diff_context=diff_context),
        agent=agent,
        expected_output=f"A JSON array of {agent_name.lower()} findings.",
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    
    result = crew.kickoff()
    return str(result)


def run_review_pipeline(structured_diff: Dict[str, Any]) -> Dict[str, Any]:
    """Run the CrewAI review pipeline on a structured diff with parallel execution.
    """
    import json
    import re
    from time import time

    start_time = time()
    logger.info("Starting review pipeline with parallel execution")
    
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

    # Run 4 review agents in parallel using ThreadPoolExecutor
    logger.info("Running 4 review agents in parallel")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_run_single_agent_task, readability_agent, READABILITY_DESC, diff_context, "ReadabilityAgent"): "readability",
            executor.submit(_run_single_agent_task, logic_agent, LOGIC_DESC, diff_context, "LogicAgent"): "logic",
            executor.submit(_run_single_agent_task, performance_agent, PERFORMANCE_DESC, diff_context, "PerformanceAgent"): "performance",
            executor.submit(_run_single_agent_task, security_agent, SECURITY_DESC, diff_context, "SecurityAgent"): "security",
        }
        
        # Collect results as they complete
        agent_results = {}
        for future in futures:
            agent_type = futures[future]
            try:
                result = future.result()
                agent_results[agent_type] = result
                logger.info(f"{agent_type.capitalize()}Agent completed")
            except Exception as e:
                logger.error(f"{agent_type.capitalize()}Agent failed: {str(e)}")
                agent_results[agent_type] = "[]"
    
    parallel_time = time() - start_time
    logger.info(f"Parallel execution completed in {parallel_time:.2f}s")
    
    # Parse results from all agents
    all_comments = []
    for agent_type, result_str in agent_results.items():
        json_match = re.search(r"```json\s*\n(.*?)\n```", result_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = result_str
        
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                all_comments.extend(parsed)
            elif isinstance(parsed, dict) and "comments" in parsed:
                all_comments.extend(parsed["comments"])
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse {agent_type} agent output as JSON")
    
    # Deduplicate and merge results programmatically instead of using consolidation agent
    logger.info("Deduplicating and merging findings")
    
    # Simple deduplication: remove duplicates based on file, line, and issue similarity
    seen = set()
    comments = []
    
    for comment in all_comments:
        # Create a key for deduplication
        key = (
            comment.get("file", ""),
            comment.get("line", 0),
            comment.get("issue", "")[:50]  # First 50 chars of issue
        )
        
        if key not in seen:
            seen.add(key)
            comments.append(comment)
    
    total_time = time() - start_time
    
    log_with_context(
        logger, "info", "Review pipeline completed",
        total_time_seconds=round(total_time, 2),
        parallel_time_seconds=round(parallel_time, 2),
        total_issues=len(comments),
        critical=len([c for c in comments if c.get("severity") == "critical"]),
        error=len([c for c in comments if c.get("severity") == "error"]),
        warning=len([c for c in comments if c.get("severity") == "warning"]),
        info=len([c for c in comments if c.get("severity") in ["info", "low", "medium", "moderate", "high"]])
    )
    
    return {"comments": comments}
