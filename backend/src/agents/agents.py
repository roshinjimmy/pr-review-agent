from crewai import Agent

MODEL_ID = "openrouter/openai/gpt-4o-mini"

readability_agent = Agent(
    role="Readability Reviewer",
    goal="Identify readability issues in the changed code segments",
    backstory=(
        "You are a code review specialist focused on readability. "
        "You pay attention to naming, comments, formatting, and overall clarity "
        "to ensure code is easy to understand and maintain."
    ),
    llm=MODEL_ID,
    allow_delegation=False,
    verbose=False,
)


logic_agent = Agent(
    role="Logic & Bug Reviewer",
    goal="Detect logical errors, missing edge cases, and potential bugs",
    backstory=(
        "You are an experienced backend engineer who reviews code for logical "
        "correctness. You carefully reason about branches, edge cases, and "
        "error handling."
    ),
    llm=MODEL_ID,
    allow_delegation=False,
    verbose=False,
)


performance_agent = Agent(
    role="Performance Reviewer",
    goal="Spot performance issues in the changed code",
    backstory=(
        "You specialize in performance. You look for inefficient loops, "
        "redundant operations, and unnecessary computations, and suggest "
        "simpler, faster alternatives where possible."
    ),
    llm=MODEL_ID,
    allow_delegation=False,
    verbose=False,
)


security_agent = Agent(
    role="Security Reviewer",
    goal="Identify security risks in the changed code",
    backstory=(
        "You are a security-focused engineer. You scan for unsafe patterns, "
        "insecure API usage, injection risks, and hardcoded secrets."
    ),
    llm=MODEL_ID,
    allow_delegation=False,
    verbose=False,
)


consolidation_agent = Agent(
    role="Consolidation Reviewer",
    goal="Merge and deduplicate findings from all other agents",
    backstory=(
        "You act as a lead reviewer who sees all individual findings and "
        "produces a clean, consolidated review suitable for GitHub comments."
    ),
    llm=MODEL_ID,
    allow_delegation=False,
    verbose=False,
)