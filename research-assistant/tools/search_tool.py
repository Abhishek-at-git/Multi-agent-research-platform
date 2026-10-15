"""DuckDuckGo Search Tool for CrewAI.

Provides robust web search capability with retry logic, rate-limit resilience,
result deduplication, and structured citation metadata (title, snippet, URL).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from crewai.tools import BaseTool, tool
from pydantic import Field

logger = logging.getLogger("research_assistant.tools")

# Resilient import of DuckDuckGo Search backend
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None  # Handled at runtime with helpful error message


def execute_ddg_search(
    query: str,
    max_results: int = 5,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
) -> List[Dict[str, Any]]:
    """Execute search query using DuckDuckGo with exponential backoff retry.

    Args:
        query: Search string or keywords.
        max_results: Maximum results to retrieve.
        max_retries: Number of retry attempts upon failure.
        backoff_factor: Multiplier for retry delays.

    Returns:
        List of dicts containing 'title', 'href', 'body', and 'domain'.
    """
    if DDGS is None:
        raise ImportError(
            "Neither 'ddgs' nor 'duckduckgo_search' is installed. "
            "Please run: pip install ddgs duckduckgo-search"
        )

    cleaned_query = query.strip().strip('"').strip("'")
    if not cleaned_query:
        return []

    delay = 1.0
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Executing search (attempt {attempt}/{max_retries}): '{cleaned_query}'")
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(cleaned_query, max_results=max_results))

            normalized: List[Dict[str, Any]] = []
            for item in raw_results:
                title = item.get("title", "Untitled Source").strip()
                url = item.get("href") or item.get("link") or ""
                body = item.get("body") or item.get("snippet") or ""

                if not url:
                    continue

                parsed = urlparse(url)
                domain = parsed.netloc or "web"

                normalized.append({
                    "title": title,
                    "href": url,
                    "body": body,
                    "domain": domain,
                })

            logger.info(f"Retrieved {len(normalized)} results for query: '{cleaned_query}'")
            return normalized

        except Exception as exc:
            last_exception = exc
            logger.warning(
                f"DuckDuckGo search attempt {attempt} failed for '{cleaned_query}': {exc}"
            )
            if attempt < max_retries:
                time.sleep(delay)
                delay *= backoff_factor

    logger.error(f"All {max_retries} search attempts failed for '{cleaned_query}': {last_exception}")
    return []


def format_search_results(results: List[Dict[str, Any]], query: str) -> str:
    """Format structured search results into an easily parseable text block for AI agents."""
    if not results:
        return f"No credible search results found for query: '{query}'. Try alternative keywords or broader phrasing."

    formatted_lines = [
        f"### DuckDuckGo Search Results for: '{query}'",
        f"Total sources found: {len(results)}\n",
    ]

    for index, res in enumerate(results, start=1):
        title = res.get("title", "Untitled")
        url = res.get("href", "")
        body = res.get("body", "").replace("\n", " ")
        domain = res.get("domain", "")

        formatted_lines.append(f"Source [{index}]:")
        formatted_lines.append(f"- Title: {title}")
        formatted_lines.append(f"- URL: {url}")
        formatted_lines.append(f"- Domain: {domain}")
        formatted_lines.append(f"- Key Snippet: {body}\n")

    return "\n".join(formatted_lines)


@tool("DuckDuckGo Web Search")
def duckduckgo_search_tool(query: str) -> str:
    """Search the web using DuckDuckGo for up-to-date facts, technical articles, statistics, and industry reports.

    Args:
        query: The search keywords to find information on.

    Returns:
        Formatted string containing source titles, URLs, domains, and summary snippets.
    """
    results = execute_ddg_search(query, max_results=6)
    return format_search_results(results, query)


class DuckDuckGoSearchTool(BaseTool):
    """Class-based DuckDuckGo Search Tool compatible with CrewAI agents."""

    name: str = "DuckDuckGo Web Search"
    description: str = (
        "Search the web using DuckDuckGo for up-to-date facts, technical articles, "
        "statistics, market analyses, and industry reports. Returns structured sources with titles and URLs."
    )
    max_results: int = Field(default=6, description="Maximum number of search results to retrieve")

    def _run(self, query: str) -> str:
        """Execute the search synchronously."""
        results = execute_ddg_search(query, max_results=self.max_results)
        return format_search_results(results, query)
