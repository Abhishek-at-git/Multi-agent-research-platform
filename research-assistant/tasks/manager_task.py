"""Manager Task definitions.

Defines the scoping and executive review tasks overseen by the Manager Agent.
"""

from __future__ import annotations

from typing import List, Optional
from crewai import Agent, Task


def create_scoping_task(agent: Agent, topic: str) -> Task:
    """Create the initial research scoping and directive task.

    Args:
        agent: The Manager Agent.
        topic: The research subject.

    Returns:
        Task: Configured scoping task.
    """
    description = (
        f"Define the strategic research charter for the topic: '{topic}'.\n\n"
        "Your objectives:\n"
        "1. Identify the 4-5 most critical dimensions of this topic (technological, commercial, "
        "operational, regulatory/ethical, and future outlook).\n"
        "2. Formulate explicit investigative instructions for the Search and Analysis Agents.\n"
        "3. Specify key metrics or benchmark areas that must be researched.\n"
        "4. Set quality benchmarks for the final report deliverable."
    )

    expected_output = (
        "A formal Research Charter outlining:\n"
        "- Core Research Questions & Objectives\n"
        "- 4-5 Key Inquiry Dimensions\n"
        "- Recommended Search Vectors\n"
        "- Executive Quality Criteria"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )


def create_review_task(
    agent: Agent,
    topic: str,
    context_tasks: Optional[List[Task]] = None,
    output_file: Optional[str] = None,
) -> Task:
    """Create the final executive sign-off and synthesis review task.

    Args:
        agent: The Manager Agent.
        topic: The research subject.
        context_tasks: Prior tasks (notably the writing_task).
        output_file: Path to save reviewed report.

    Returns:
        Task: Configured review task.
    """
    description = (
        f"Perform executive review and final sign-off on the generated research report for: '{topic}'.\n\n"
        "Review Checklist:\n"
        "1. Verify that all 7 required sections are complete and thoroughly developed.\n"
        "2. Check that in-text citations [1], [2] correctly correspond to the References table.\n"
        "3. Ensure the tone is authoritative, objective, and executive-ready.\n"
        "4. If any minor improvements or polish are required, incorporate them into the final Markdown.\n"
        "5. Output the definitive version of the report."
    )

    expected_output = (
        "The finalized, executive-reviewed, and polished Markdown report ready for distribution."
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks or [],
        output_file=output_file,
    )
