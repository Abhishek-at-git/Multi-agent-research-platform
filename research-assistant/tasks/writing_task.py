"""Writing Task definition.

Directs the Writer Agent to craft the final, production-ready research report
incorporating all required sections, citation formatting, and language localization.
"""

from __future__ import annotations

from typing import List, Optional
from crewai import Agent, Task


def create_writing_task(
    agent: Agent,
    topic: str,
    context_tasks: Optional[List[Task]] = None,
    language: str = "English",
    output_file: Optional[str] = None,
) -> Task:
    """Create the report generation task.

    Args:
        agent: The Writer Agent assigned to draft the report.
        topic: The research subject.
        context_tasks: List of predecessor tasks (e.g., analysis_task).
        language: Target natural language for the final report.
        output_file: Optional filepath to automatically save the markdown report.

    Returns:
        Task: Configured writing task.
    """
    description = (
        f"Draft a comprehensive, executive-grade research report on the topic: '{topic}'.\n\n"
        f"Target Language: Write the entire report in **{language}**.\n\n"
        "Your report must follow this exact Markdown structure:\n\n"
        "# [Compelling, Professional Report Title]\n\n"
        "> **Research Topic:** {topic} | **Language:** {language} | **Status:** Production-Ready\n\n"
        "## 1. Executive Summary\n"
        "- A concise 2-3 paragraph executive briefing summarizing the core thesis, magnitude of impact, "
        "and primary strategic takeaway.\n\n"
        "## 2. Market & Technology Overview\n"
        "- Clear definition of core concepts, technological taxonomy, and historical/current context.\n\n"
        "## 3. Key Findings & Trends\n"
        "- Verified trends, recent breakthroughs, and quantifiable metrics with in-text citation anchors [1], [2].\n"
        "- Include at least one comparison table or structured metrics breakdown.\n\n"
        "## 4. Detailed Analysis\n"
        "### 4.1 Benefits & High-Value Use Cases\n"
        "- Concrete real-world applications, productivity or business impact, and success stories.\n"
        "### 4.2 Challenges, Bottlenecks & Risk Factors\n"
        "- Technical constraints, security, governance, financial costs, or ethical risks.\n\n"
        "## 5. Strategic Recommendations & Future Outlook\n"
        "- 1-to-5-year forecast, roadmap recommendations for practitioners and decision-makers.\n\n"
        "## 6. Conclusion\n"
        "- Definitive closing perspective summarizing the ultimate trajectory.\n\n"
        "## 7. Sources & References\n"
        "- A clean Markdown table listing all cited sources with this schema:\n"
        "| Citation | Source Title | Domain / Organization | URL |\n"
        "| :---: | :--- | :--- | :--- |\n"
        "| [1] | ... | ... | ... |\n\n"
        "Style & Quality Guidelines:\n"
        "- Professional, authoritative, and engaging tone.\n"
        "- Embed in-text citation markers (e.g., [1], [2]) directly beside key facts.\n"
        "- Do NOT use vague placeholder text. Every section must be complete, detailed, and substantive."
    )

    expected_output = (
        f"A complete, publication-grade Markdown research report written in {language}, "
        "containing all 7 required sections, metrics tables, in-text citations [1], [2], "
        "and a fully populated References & Sources table."
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks or [],
        output_file=output_file,
    )
