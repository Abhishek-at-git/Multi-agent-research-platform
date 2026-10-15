"""Main entry point for the Multi-Agent Research Assistant.

Orchestrates Manager, Search, Analysis, and Writer agents using CrewAI and Google Gemini
to research any topic, cite sources, and output executive Markdown & PDF reports.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from crewai import Crew, Process
from config.settings import get_settings, setup_logging, get_gemini_llm
from agents.manager import create_manager_agent
from agents.search_agent import create_search_agent
from agents.analysis_agent import create_analysis_agent
from agents.writer_agent import create_writer_agent

from tasks.search_task import create_search_task
from tasks.analysis_task import create_analysis_task
from tasks.writing_task import create_writing_task
from tasks.manager_task import create_scoping_task, create_review_task

from utils.db import save_report, init_db, list_reports, get_db_stats
from utils.pdf_exporter import export_markdown_to_pdf

console = Console()
logger = setup_logging()

SUGGESTED_TOPICS = [
    "AI Agents in Software Engineering and Developer Productivity",
    "Generative AI in Healthcare Diagnostics and Drug Discovery",
    "Cloud Computing Serverless Architectures & Edge AI 2025-2026",
    "Full Stack Development with WebAssembly, Rust, and Next.js",
    "Early-Stage AI Startups: Valuation Multiples, Capital Efficiency & Unit Economics",
]


def slugify(text: str) -> str:
    """Convert string to safe filename slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text).strip("_")[:45]


def display_welcome_banner():
    """Print visually striking banner with rich styling."""
    title = Text("MULTI-AGENT RESEARCH ASSISTANT", style="bold cyan")
    subtitle = Text(
        "Powered by CrewAI, Google Gemini & DuckDuckGo Search",
        style="dim white",
    )
    panel = Panel(
        Text.assemble(
            title, "\n", subtitle, "\n\n",
            Text("Collaborative AI Agents: ", style="bold green"),
            Text("Manager -> Search Agent -> Analysis Agent -> Writer Agent", style="yellow"),
        ),
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(panel)


def check_api_key_prompt(settings) -> str:
    """Validate or interactively prompt for Gemini API Key if missing."""
    key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if not key or key.strip() in ("", "your_gemini_api_key_here"):
        console.print(
            Panel(
                "[bold red]GEMINI_API_KEY Not Found![/bold red]\n\n"
                "To use Gemini models, a valid Google Gemini API Key is required.\n"
                "You can obtain a free key at: [bold underline cyan]https://aistudio.google.com/app/apikey[/bold underline cyan]",
                border_style="red",
            )
        )
        key = Prompt.ask("[bold yellow]Enter your GEMINI_API_KEY[/bold yellow]", password=True)
        if not key or not key.strip():
            console.print("[bold red]API key cannot be empty. Exiting.[/bold red]")
            sys.exit(1)
        os.environ["GEMINI_API_KEY"] = key.strip()
    return key.strip()


def run_research_crew(
    topic: str,
    language: str = "English",
    model_name: Optional[str] = None,
    process_mode: str = "sequential",
    export_pdf: bool = True,
    verbose: bool = True,
) -> dict:
    """Orchestrate the research assistant crew.

    Args:
        topic: Research topic query.
        language: Language for the generated report.
        model_name: Gemini model name.
        process_mode: 'sequential' or 'hierarchical'.
        export_pdf: Whether to generate a styled PDF report.
        verbose: Verbose terminal output during crew execution.

    Returns:
        dict: Execution results containing report markdown, paths, word count, and metadata.
    """
    settings = get_settings()
    init_db()

    # Determine output filepaths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(topic)

    primary_report_path = settings.outputs_dir / "report.md"
    archived_report_path = settings.reports_dir / f"report_{slug}_{timestamp}.md"
    pdf_report_path = settings.reports_dir / f"report_{slug}_{timestamp}.pdf"

    console.print(f"\n[bold cyan]Initializing AI Agents with model:[/bold cyan] [green]{model_name or settings.gemini_model}[/green]")
    console.print(f"[bold cyan]Research Topic:[/bold cyan] [bold yellow]{topic}[/bold yellow]")
    console.print(f"[bold cyan]Report Language:[/bold cyan] [magenta]{language}[/magenta]")
    console.print(f"[bold cyan]Orchestration Mode:[/bold cyan] [cyan]{process_mode.capitalize()}[/cyan]\n")

    # Instantiate LLM
    llm = get_gemini_llm(model_name=model_name)

    # Initialize specialized agents
    manager_agent = create_manager_agent(llm=llm, verbose=verbose)
    search_agent = create_search_agent(llm=llm, verbose=verbose)
    analysis_agent = create_analysis_agent(llm=llm, verbose=verbose)
    writer_agent = create_writer_agent(llm=llm, verbose=verbose)

    # Define tasks with pipeline dependency context
    scoping_task = create_scoping_task(agent=manager_agent, topic=topic)

    search_task = create_search_task(agent=search_agent, topic=topic)

    analysis_task = create_analysis_task(
        agent=analysis_agent,
        topic=topic,
        context_tasks=[search_task],
    )

    writing_task = create_writing_task(
        agent=writer_agent,
        topic=topic,
        context_tasks=[analysis_task],
        language=language,
        output_file=str(primary_report_path),
    )

    review_task = create_review_task(
        agent=manager_agent,
        topic=topic,
        context_tasks=[writing_task],
        output_file=str(archived_report_path),
    )

    # Build Crew
    if process_mode.lower() == "hierarchical":
        crew = Crew(
            agents=[search_agent, analysis_agent, writer_agent],
            tasks=[search_task, analysis_task, writing_task],
            process=Process.hierarchical,
            manager_agent=manager_agent,
            verbose=verbose,
        )
    else:
        # Sequential pipeline with manager initiation and review
        crew = Crew(
            agents=[manager_agent, search_agent, analysis_agent, writer_agent],
            tasks=[scoping_task, search_task, analysis_task, writing_task, review_task],
            process=Process.sequential,
            verbose=verbose,
        )

    start_time = time.time()
    console.print("[bold green]Starting autonomous research mission...[/bold green]\n")

    try:
        crew_output = crew.kickoff()
        execution_time = time.time() - start_time
    except Exception as exc:
        logger.error(f"Crew execution encountered an error: {exc}", exc_info=True)
        console.print(f"\n[bold red]Error during Crew execution:[/bold red] {exc}")
        raise exc

    # Retrieve generated markdown
    final_markdown = ""
    if archived_report_path.exists():
        final_markdown = archived_report_path.read_text(encoding="utf-8")
    elif primary_report_path.exists():
        final_markdown = primary_report_path.read_text(encoding="utf-8")
    else:
        final_markdown = str(crew_output)
        primary_report_path.write_text(final_markdown, encoding="utf-8")
        archived_report_path.write_text(final_markdown, encoding="utf-8")

    # Ensure primary report.md always has the latest content
    primary_report_path.write_text(final_markdown, encoding="utf-8")

    # Count cited sources
    sources_count = len(re.findall(r"\[\d+\]", final_markdown))

    # Export PDF if requested
    actual_pdf_path = None
    if export_pdf:
        try:
            console.print("[dim]Generating corporate PDF report...[/dim]")
            export_markdown_to_pdf(
                markdown_content=final_markdown,
                output_pdf_path=pdf_report_path,
                topic=topic,
            )
            actual_pdf_path = str(pdf_report_path)
        except Exception as exc:
            logger.warning(f"PDF generation failed: {exc}")
            console.print(f"[yellow]Warning: PDF export skipped due to: {exc}[/yellow]")

    # Persist in SQLite database
    report_id = save_report(
        topic=topic,
        report_markdown=final_markdown,
        language=language,
        model_used=model_name or settings.gemini_model,
        pdf_path=actual_pdf_path,
        sources_count=sources_count,
    )

    word_count = len(final_markdown.split())

    # Display completion summary
    summary_table = Table(title="Research Mission Deliverable Summary", border_style="green")
    summary_table.add_column("Property", style="bold cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Database Report ID", f"#{report_id}")
    summary_table.add_row("Topic", topic)
    summary_table.add_row("Language", language)
    summary_table.add_row("Execution Time", f"{execution_time:.1f} seconds")
    summary_table.add_row("Word Count", f"{word_count:,} words")
    summary_table.add_row("Primary Markdown", str(primary_report_path))
    summary_table.add_row("Archived Markdown", str(archived_report_path))
    if actual_pdf_path:
        summary_table.add_row("PDF Export", actual_pdf_path)

    console.print("\n")
    console.print(summary_table)
    console.print(f"\n[bold green]Report saved to [underline]{primary_report_path}[/underline][/bold green]\n")

    return {
        "report_id": report_id,
        "topic": topic,
        "markdown": final_markdown,
        "primary_path": primary_report_path,
        "archived_path": archived_report_path,
        "pdf_path": actual_pdf_path,
        "word_count": word_count,
        "execution_time": execution_time,
    }


def parse_arguments():
    """Parse CLI arguments with rich defaults."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research Assistant using CrewAI and Google Gemini.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default=None,
        help="Research topic or question to investigate.",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="English",
        help="Language for the generated report (e.g. English, Spanish, French, German, Hindi).",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Gemini model identifier (e.g., gemini/gemini-2.0-flash, gemini/gemini-1.5-flash, gemini/gemini-1.5-pro).",
    )
    parser.add_argument(
        "--process", "-p",
        choices=["sequential", "hierarchical"],
        default="sequential",
        help="CrewAI process orchestration model.",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Disable automatic PDF export.",
    )
    parser.add_argument(
        "--list-reports",
        action="store_true",
        help="List previously generated reports stored in the database.",
    )
    return parser.parse_args()


def display_past_reports():
    """Display past reports stored in the SQLite database."""
    reports = list_reports(limit=20)
    stats = get_db_stats()

    if not reports:
        console.print("[yellow]No reports found in the database yet.[/yellow]")
        return

    table = Table(title="Archived Research Reports Database", border_style="cyan")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Date", style="dim")
    table.add_column("Topic", style="bold white")
    table.add_column("Language", style="magenta")
    table.add_column("Words", justify="right")
    table.add_column("PDF", style="green")

    for rep in reports:
        table.add_row(
            str(rep["id"]),
            str(rep["created_at"])[:16],
            rep["topic"][:45] + ("..." if len(rep["topic"]) > 45 else ""),
            rep.get("language", "English"),
            f"{rep.get('word_count', 0):,}",
            "[green]Yes[/green]" if rep.get("pdf_path") else "[dim]No[/dim]",
        )

    console.print(table)
    console.print(
        f"[dim]Total Reports: {stats.get('total_reports', 0)} | Total Words: {stats.get('total_words', 0):,}[/dim]\n"
    )


def main():
    """Main CLI execution routine."""
    display_welcome_banner()
    args = parse_arguments()
    settings = get_settings()

    if args.list_reports:
        display_past_reports()
        return

    # Check / prompt for API key
    check_api_key_prompt(settings)

    topic = args.topic
    if not topic:
        console.print("\n[bold cyan]Select a Research Topic or enter your own:[/bold cyan]")
        for i, sug in enumerate(SUGGESTED_TOPICS, 1):
            console.print(f"  [bold green][{i}][/bold green] {sug}")
        console.print("  [bold green][0][/bold green] Enter custom research topic")

        choice = Prompt.ask("\nChoose an option [0-5]", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(SUGGESTED_TOPICS):
            topic = SUGGESTED_TOPICS[int(choice) - 1]
        else:
            topic = Prompt.ask("\n[bold yellow]Enter research topic / query[/bold yellow]")

    if not topic.strip():
        console.print("[red]Topic cannot be empty. Exiting.[/red]")
        sys.exit(1)

    export_pdf = not args.no_pdf
    language = args.language

    run_research_crew(
        topic=topic.strip(),
        language=language,
        model_name=args.model,
        process_mode=args.process,
        export_pdf=export_pdf,
        verbose=True,
    )


if __name__ == "__main__":
    main()
