"""Analysis Task definition.

Directs the Analysis Agent to critically evaluate search findings,
filter noise, extract quantifiable metrics, identify trends,
and organize insights for the writer agent.
"""

from __future__ import annotations

from typing import List, Optional
from crewai import Agent, Task


def create_analysis_task(
    agent: Agent,
    topic: str,
    context_tasks: Optional[List[Task]] = None,
) -> Task:
    """Create the synthesis and data analysis task.

    Args:
        agent: The Analysis Agent assigned to execute this task.
        topic: The research subject.
        context_tasks: Optional list of prerequisite tasks (e.g., search_task).

    Returns:
        Task: Configured analysis task.
    """
    description = (
        f"Critically analyze the research dossier gathered on the topic: '{topic}'.\n\n"
        "Your objectives:\n"
        "1. Filter and Deduplicate:\n"
        "   - Remove redundant information, marketing hype, or unsubstantiated claims.\n"
        "   - Verify that claims are backed by credible web sources.\n\n"
        "2. Extract Quantitative Data & Metrics:\n"
        "   - Identify growth figures, adoption percentages, dollar values, benchmarks, and dates.\n"
        "   - Tabulate key metrics where relevant.\n\n"
        "3. Synthesize Strategic Themes:\n"
        "   - Market Drivers & Technological Shifts: What is propelling change?\n"
        "   - High-Impact Benefits: Where is measurable value being created?\n"
        "   - Critical Risks & Bottlenecks: Technical limitations, ethical concerns, or integration hurdles.\n"
        "   - Competitive Landscape / Frameworks: Key technologies or ecosystem leaders.\n"
        "   - Future Predictions: 1-5 year outlook based on expert consensus.\n\n"
        "4. Structure Citation Mapping:\n"
        "   - Maintain an indexed list of sources [1], [2], etc., matching each claim to its URL and title."
    )

    expected_output = (
        "A rigorous analytical briefing containing:\n"
        "- Executive Takeaways (3-5 high-level bullet points)\n"
        "- Verified Quantitative Statistics & Market Figures\n"
        "- Thematic Analysis (Drivers, Benefits, Risks/Bottlenecks, Future Outlook)\n"
        "- Indexed Source Map ([1], [2], [3] with Title and exact URL) for the Writer Agent"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks or [],
    )
