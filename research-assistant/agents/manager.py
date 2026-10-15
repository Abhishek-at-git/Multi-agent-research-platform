"""Manager Agent module.

The Manager Agent acts as the research director, breaking down the user's research
query into structured inquiries, coordinating specialized agents, and ensuring
the final report satisfies rigorous executive quality benchmarks.
"""

from __future__ import annotations

from typing import Optional
from crewai import Agent, LLM
from config.settings import get_gemini_llm


def create_manager_agent(
    llm: Optional[LLM] = None,
    verbose: bool = True,
    allow_delegation: bool = True,
) -> Agent:
    """Create and return the Manager Agent.

    Args:
        llm: Optional CrewAI LLM instance. Defaults to configured Gemini LLM.
        verbose: Whether agent outputs detailed thought steps to console.
        allow_delegation: Allow manager to delegate tasks to other agents.

    Returns:
        Agent: Configured Manager Agent.
    """
    resolved_llm = llm or get_gemini_llm()

    return Agent(
        role="Research Director & Project Manager",
        goal=(
            "Coordinate the end-to-end research workflow for any requested topic. "
            "Decompose high-level topics into strategic inquiry vectors, guide the search "
            "and analytical agents, and synthesize all findings into a cohesive, world-class executive report."
        ),
        backstory=(
            "You are a seasoned Research Director at an elite global strategic intelligence consultancy. "
            "You have spent decades managing cross-functional teams of investigative scouts, quantitative analysts, "
            "and principal technical writers. You have an eagle eye for factual integrity, logical structure, "
            "clarity, and actionable strategic foresight. You never settle for surface-level summaries; "
            "you demand deep insights, verifiable statistics, credible citations, and definitive conclusions."
        ),
        llm=resolved_llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
        memory=False,
    )
