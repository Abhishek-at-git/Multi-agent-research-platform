"""Writer Agent module.

The Writer Agent crafts publication-ready research reports with
Executive Summary, Key Findings, Detailed Analysis, Conclusion,
and professional citation formatting in the target language.
"""

from __future__ import annotations

from typing import Optional
from crewai import Agent, LLM
from config.settings import get_gemini_llm


def create_writer_agent(
    llm: Optional[LLM] = None,
    verbose: bool = True,
) -> Agent:
    """Create and return the Writer Agent.

    Args:
        llm: Optional CrewAI LLM instance. Defaults to configured Gemini LLM.
        verbose: Whether agent outputs execution details to console.

    Returns:
        Agent: Configured Writer Agent.
    """
    resolved_llm = llm or get_gemini_llm()

    return Agent(
        role="Principal Technical Author & Executive Report Writer",
        goal=(
            "Transform analytical insights on {topic} into an authoritative, beautifully structured, "
            "production-grade research report in {language}. "
            "Ensure the report features an Executive Summary, Market Overview, Key Trends, "
            "In-depth Technical Analysis, Benefits & Risks, Future Outlook, and formatted Citations."
        ),
        backstory=(
            "You are an acclaimed technical author and former chief editor for leading research publications "
            "and technology journals. You have an exceptional ability to write clear, compelling, "
            "and authoritative markdown reports. You use precise section headers, bulleted takeaways, "
            "comparison tables, callout blocks, and rigorous in-text citations [1], [2] linked to a complete "
            "References section. Your prose is sophisticated, engaging, factual, and devoid of generic clichés."
        ),
        llm=resolved_llm,
        verbose=verbose,
        allow_delegation=False,
        memory=False,
    )
