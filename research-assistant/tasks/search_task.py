"""Search Task definition.

Directs the Search Agent to conduct multi-faceted web inquiries on the research topic,
retrieving credible facts, recent news, statistics, and authoritative URLs.
"""

from __future__ import annotations

from typing import Optional
from crewai import Agent, Task


def create_search_task(agent: Agent, topic: str) -> Task:
    """Create the information retrieval and web search task.

    Args:
        agent: The Search Agent assigned to execute this task.
        topic: The research subject.

    Returns:
        Task: Configured search task.
    """
    description = (
        f"Conduct comprehensive web research on the topic: '{topic}'.\n\n"
        "Your objectives:\n"
        "1. Perform at least 3-4 targeted searches using the DuckDuckGo Search Tool to cover:\n"
        "   - Current landscape, definitions, and foundational concepts.\n"
        "   - Recent breakthroughs, industry adoption numbers, and market growth statistics.\n"
        "   - Key real-world benefits, case studies, and concrete examples.\n"
        "   - Major challenges, criticisms, bottlenecks, or security/ethical risks.\n"
        "   - Leading companies, frameworks, and future trajectory.\n\n"
        "2. For every search result, capture:\n"
        "   - Source Title\n"
        "   - Exact URL\n"
        "   - Publishing Domain/Organization\n"
        "   - Concrete factual summary, relevant statistics, and key quotes.\n\n"
        "3. Ensure your findings are recent, authoritative, and fact-based.\n"
        "Preserve ALL URLs carefully so subsequent agents can reference and cite them."
    )

    expected_output = (
        "A structured, multi-section research dossier containing:\n"
        "- Grouped research sections (Landscape, Statistics/Metrics, Case Studies, Challenges, Future Outlook)\n"
        "- Fact-dense bullet points with numerical data\n"
        "- Complete list of referenced sources with Title, URL, and Domain"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )
