"""Search Agent module.

The Search Agent conducts web inquiries using DuckDuckGo, gathers up-to-date
facts, finds authoritative sources, and structures findings with source attribution.
"""

from __future__ import annotations

from typing import List, Optional
from crewai import Agent, LLM
from config.settings import get_gemini_llm
from tools.search_tool import duckduckgo_search_tool


def create_search_agent(
    llm: Optional[LLM] = None,
    tools: Optional[List] = None,
    verbose: bool = True,
) -> Agent:
    """Create and return the Search Agent equipped with DuckDuckGo search tool.

    Args:
        llm: Optional CrewAI LLM instance. Defaults to configured Gemini LLM.
        tools: Optional list of tools. Defaults to [duckduckgo_search_tool].
        verbose: Whether agent outputs execution details to console.

    Returns:
        Agent: Configured Search Agent.
    """
    resolved_llm = llm or get_gemini_llm()
    resolved_tools = tools if tools is not None else [duckduckgo_search_tool]

    return Agent(
        role="Lead Web Research & Intelligence Scout",
        goal=(
            "Execute thorough, multi-angled web searches on {topic}. "
            "Identify authoritative industry sources, recent announcements, real-world case studies, "
            "and quantifiable data. Return comprehensive findings with full URLs, titles, and publication context."
        ),
        backstory=(
            "You are a master intelligence scout and technical investigator. "
            "You know how to formulate precise search queries across technical blogs, academic papers, "
            "industry whitepapers, GitHub repos, and news outlets. You never rely on a single shallow search; "
            "you explore sub-queries, emerging angles, counter-arguments, and recent developments. "
            "Crucially, you always preserve and record exact URLs and source titles so every insight can be verified."
        ),
        tools=resolved_tools,
        llm=resolved_llm,
        verbose=verbose,
        allow_delegation=False,
        memory=False,
    )
