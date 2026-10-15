"""Analysis Agent module.

The Analysis Agent critically evaluates gathered research, filters out noise
and duplicates, extracts verifiable metrics, trends, and strategic implications,
and synthesizes them into an organized analytical foundation.
"""

from __future__ import annotations

from typing import Optional
from crewai import Agent, LLM
from config.settings import get_gemini_llm


def create_analysis_agent(
    llm: Optional[LLM] = None,
    verbose: bool = True,
) -> Agent:
    """Create and return the Analysis Agent.

    Args:
        llm: Optional CrewAI LLM instance. Defaults to configured Gemini LLM.
        verbose: Whether agent outputs execution details to console.

    Returns:
        Agent: Configured Analysis Agent.
    """
    resolved_llm = llm or get_gemini_llm()

    return Agent(
        role="Senior Research Analyst & Data Synthesizer",
        goal=(
            "Critically analyze raw search dossiers on {topic}. "
            "Eliminate redundancy, detect marketing fluff, extract concrete statistical metrics, "
            "identify emerging market trends, map pros & cons, and synthesize cross-domain takeaways "
            "with indexed source references."
        ),
        backstory=(
            "You are a rigorous quantitative and strategic analyst known for cutting through noise "
            "to extract pure substance. You have analyzed thousands of technology shifts, market disruptions, "
            "and software paradigms. When presented with web findings, you cross-check conflicting claims, "
            "aggregate data points, calculate percentages and growth rates where available, and construct "
            "clear thematic clusters: market drivers, technical architectures, real-world benefits, "
            "critical bottlenecks, and future trajectory."
        ),
        llm=resolved_llm,
        verbose=verbose,
        allow_delegation=False,
        memory=False,
    )
