"""Streamlit Web Application for Multi-Agent Research Assistant.

Provides an interactive GUI for running research crews, monitoring agent progress,
viewing formatted reports with citations, exporting PDF documents, and exploring
archived reports in the SQLite database.
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import streamlit as st
from config.settings import get_settings
from main import run_research_crew, SUGGESTED_TOPICS
from utils.db import list_reports, get_report, delete_report, get_db_stats
from utils.pdf_exporter import export_markdown_to_pdf

# Set page config
st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern visual polish
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-card {
        display: inline-block;
        padding: 4px 12px;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
        margin-right: 8px;
    }
    .agent-pill {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    .report-card {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_active_api_key():
    """Retrieve API key from session state, env, or settings."""
    if "api_key" in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    settings = get_settings()
    return settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")


# ---------------- SIDEBAR CONFIGURATION ----------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/artificial-intelligence.png", width=64)
    st.title("Settings & Control")

    # API Key Input
    saved_key = get_active_api_key()
    user_api_key = st.text_input(
        "Google Gemini API Key",
        value=saved_key,
        type="password",
        help="Get a free key at https://aistudio.google.com/app/apikey",
    )
    if user_api_key:
        st.session_state.api_key = user_api_key.strip()
        os.environ["GEMINI_API_KEY"] = user_api_key.strip()

    if not user_api_key:
        st.warning("⚠️ Enter your Gemini API Key to enable research.")

    st.markdown("---")
    st.subheader("Model & Orchestration")

    model_options = [
        "gemini/gemini-3.8-flash",
        "gemini/gemini-3.6-flash",
        "gemini/gemini-3.5-flash",
        "gemini/gemini-3.8-flash-lite",
        "gemini/gemini-3.1-flash-lite",
        "Custom Model",
    ]
    current_default_model = get_settings().gemini_model
    # Match default index if present in model_options
    default_idx = 0
    for idx, opt in enumerate(model_options):
        if opt == current_default_model or opt.endswith(current_default_model):
            default_idx = idx
            break

    selected_model = st.selectbox("Gemini Model", options=model_options, index=default_idx)
    if selected_model == "Custom Model":
        custom_model = st.text_input("Enter model name (e.g., gemini/gemini-3.8-flash)")
        chosen_model = custom_model if custom_model else "gemini/gemini-3.8-flash"
    else:
        chosen_model = selected_model

    temperature = st.slider(
        "Sampling Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        help="Lower values yield more factual, analytical outputs.",
    )

    language_options = [
        "English",
        "Spanish",
        "French",
        "German",
        "Hindi",
        "Japanese",
        "Chinese",
        "Portuguese",
        "Italian",
    ]
    selected_language = st.selectbox("Report Language", options=language_options, index=0)

    process_mode = st.radio(
        "Orchestration Process",
        options=["sequential", "hierarchical"],
        format_func=lambda x: "Sequential (Recommended)" if x == "sequential" else "Hierarchical (Manager-Delegated)",
        index=0,
    )

    st.markdown("---")
    db_stats = get_db_stats()
    st.metric("Total Archived Reports", db_stats.get("total_reports", 0))
    st.metric("Total Researched Words", f"{db_stats.get('total_words', 0):,}")


# ---------------- MAIN APPLICATION TABS ----------------
tab_new_research, tab_history, tab_about = st.tabs(
    ["🔬 New Research Mission", "📚 Archived Reports & Database", "ℹ️ System Architecture"]
)

# ---------------- TAB 1: NEW RESEARCH MISSION ----------------
with tab_new_research:
    st.markdown('<div class="main-header">Autonomous Multi-Agent Research Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Collaborative AI agents performing deep web search, data extraction, analysis, and report generation.</div>',
        unsafe_allow_html=True,
    )

    # Badges
    st.markdown(
        """
        <span class="badge-card">🤖 CrewAI 1.15+</span>
        <span class="badge-card">⚡ Google Gemini</span>
        <span class="badge-card">🔎 DuckDuckGo Search</span>
        <span class="badge-card">📄 Markdown & PDF Export</span>
        <span class="badge-card">🗄️ SQLite Database</span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Topic Suggestions
    st.markdown("**Quick Topics:**")
    cols = st.columns(len(SUGGESTED_TOPICS))
    for idx, (col, sug) in enumerate(zip(cols, SUGGESTED_TOPICS)):
        short_title = sug.split(":")[0].split("in")[0].split("with")[0].strip()
        if col.button(f"💡 {short_title[:18]}", key=f"sug_{idx}"):
            st.session_state.selected_topic = sug

    # Topic Input
    initial_topic = st.session_state.get(
        "selected_topic", "Research the impact of AI Agents in software engineering jobs."
    )
    topic_input = st.text_area(
        "Research Topic / Inquiry Query:",
        value=initial_topic,
        height=85,
        placeholder="e.g. Research the impact of AI Agents in software engineering jobs.",
    )

    col_btn, col_pdf_opt, col_spacer = st.columns([2, 2, 4])
    with col_btn:
        start_btn = st.button("🚀 Start Autonomous Research", type="primary", use_container_width=True)
    with col_pdf_opt:
        auto_pdf = st.checkbox("Generate PDF Report automatically", value=True)

    if start_btn:
        active_key = get_active_api_key()
        if not active_key:
            st.error("Please enter your Google Gemini API Key in the left sidebar to proceed.")
        elif not topic_input.strip():
            st.error("Please specify a research topic.")
        else:
            status_box = st.status("🤖 AI Agents Mission in Progress...", expanded=True)
            with status_box:
                st.write("📋 **Manager Agent**: Scoping research charter and formulating inquiry dimensions...")
                st.write("🌐 **Search Agent**: Scouting DuckDuckGo for credible facts, recent articles, and URLs...")
                st.write("📊 **Analysis Agent**: Evaluating findings, extracting quantitative metrics, eliminating noise...")
                st.write(f"✍️ **Writer Agent**: Drafting publication-ready report in **{selected_language}**...")

                try:
                    result = run_research_crew(
                        topic=topic_input.strip(),
                        language=selected_language,
                        model_name=chosen_model,
                        process_mode=process_mode,
                        export_pdf=auto_pdf,
                        verbose=False,
                    )
                    status_box.update(
                        label="✅ Research Mission Completed Successfully!",
                        state="complete",
                        expanded=False,
                    )
                    st.session_state["latest_result"] = result
                    st.success(f"Report #{result['report_id']} generated in {result['execution_time']:.1f}s!")
                except Exception as exc:
                    status_box.update(label="❌ Research Failed", state="error", expanded=True)
                    st.error(f"Execution Error: {exc}")

    # Display Current Report if available
    latest_result = st.session_state.get("latest_result")
    if latest_result:
        st.markdown("---")
        st.subheader(f"📄 Generated Report: {latest_result['topic']}")

        # Action Buttons
        col_down_md, col_down_pdf, col_meta = st.columns([2, 2, 4])
        with col_down_md:
            st.download_button(
                label="📥 Download Markdown (.md)",
                data=latest_result["markdown"],
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_down_pdf:
            if latest_result.get("pdf_path") and Path(latest_result["pdf_path"]).exists():
                with open(latest_result["pdf_path"], "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📕 Download PDF Report (.pdf)",
                    data=pdf_bytes,
                    file_name=Path(latest_result["pdf_path"]).name,
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                # Generate on demand
                if st.button("Generate & Download PDF", use_container_width=True):
                    pdf_path = export_markdown_to_pdf(
                        latest_result["markdown"],
                        Path("outputs") / "report.pdf",
                        topic=latest_result["topic"],
                    )
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📥 Download Ready PDF",
                            data=f.read(),
                            file_name="report.pdf",
                            mime="application/pdf",
                        )

        with col_meta:
            st.info(
                f"Words: **{latest_result['word_count']:,}** | "
                f"Time: **{latest_result['execution_time']:.1f}s** | "
                f"Saved to: `{latest_result['primary_path']}`"
            )

        # Tabs for report presentation
        rep_tab1, rep_tab2 = st.tabs(["📖 Formatted Preview", "💻 Raw Markdown"])
        with rep_tab1:
            st.markdown(latest_result["markdown"])
        with rep_tab2:
            st.code(latest_result["markdown"], language="markdown")


# ---------------- TAB 2: ARCHIVED REPORTS & DATABASE ----------------
with tab_history:
    st.subheader("📚 Research Archives (SQLite Database)")

    search_query = st.text_input("🔍 Search archived reports by keyword or topic:", "")
    reports = list_reports(limit=50)

    if search_query.strip():
        reports = [
            r for r in reports
            if search_query.lower() in r["topic"].lower()
            or search_query.lower() in (r.get("summary") or "").lower()
        ]

    if not reports:
        st.info("No research reports found matching your criteria.")
    else:
        for rep in reports:
            with st.expander(f"#{rep['id']} | {rep['topic']} ({rep['created_at'][:10]}) - {rep.get('language', 'English')}"):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"**Model:** `{rep.get('model_used', 'N/A')}`")
                c2.write(f"**Words:** {rep.get('word_count', 0):,}")
                c3.write(f"**Sources:** {rep.get('sources_count', 0)}")
                if rep.get("pdf_path") and Path(rep["pdf_path"]).exists():
                    with open(rep["pdf_path"], "rb") as pf:
                        c4.download_button(
                            "📕 PDF",
                            data=pf.read(),
                            file_name=Path(rep["pdf_path"]).name,
                            mime="application/pdf",
                            key=f"dl_pdf_{rep['id']}",
                        )

                st.markdown(f"**Summary:** *{rep.get('summary', 'No summary')}*")

                if st.button("👁️ Load into Viewer", key=f"load_{rep['id']}"):
                    full_rep = get_report(rep["id"])
                    if full_rep:
                        st.session_state["latest_result"] = {
                            "report_id": full_rep["id"],
                            "topic": full_rep["topic"],
                            "markdown": full_rep["report_markdown"],
                            "primary_path": "outputs/report.md",
                            "pdf_path": full_rep.get("pdf_path"),
                            "word_count": full_rep.get("word_count", 0),
                            "execution_time": 0.0,
                        }
                        st.success("Loaded into main viewer tab!")


# ---------------- TAB 3: SYSTEM ARCHITECTURE ----------------
with tab_about:
    st.subheader("System Architecture & Collaborative Agent Flow")
    st.markdown(
        """
        The **Multi-Agent Research Assistant** coordinates 4 specialized AI agents using CrewAI and Google Gemini:

        ```
        +-----------------------------------------------------------------------------------+
        |                               USER RESEARCH QUERY                                 |
        +-----------------------------------------------------------------------------------+
                                                  |
                                                  v
        +-----------------------------------------------------------------------------------+
        | [1] MANAGER AGENT (Research Director)                                             |
        | - Scopes the research charter                                                     |
        | - Identifies technological, commercial, and operational inquiry vectors           |
        +-----------------------------------------------------------------------------------+
                                                  |
                                                  v
        +-----------------------------------------------------------------------------------+
        | [2] SEARCH AGENT (Information Retrieval Specialist)                               |
        | - Executes targeted queries via DuckDuckGo Search Tool                            |
        | - Extracts authoritative sources, recent news, statistics, and verified URLs      |
        +-----------------------------------------------------------------------------------+
                                                  |
                                                  v
        +-----------------------------------------------------------------------------------+
        | [3] ANALYSIS AGENT (Senior Research & Data Analyst)                               |
        | - Deduplicates information and strips marketing hype                              |
        | - Extracts quantitative metrics, adoption percentages, and cross-cutting trends   |
        | - Structures indexed citation mappings [1], [2]                                   |
        +-----------------------------------------------------------------------------------+
                                                  |
                                                  v
        +-----------------------------------------------------------------------------------+
        | [4] WRITER AGENT (Principal Technical Author)                                     |
        | - Authors executive-grade Markdown report with 7 mandatory sections               |
        | - Synthesizes Executive Summary, Key Trends, Detailed Analysis, Outlook           |
        | - Embeds in-text citations and formats complete References & Sources table        |
        +-----------------------------------------------------------------------------------+
                                                  |
                                                  v
        +-----------------------------------------------------------------------------------+
        | OUTPUT PIPELINE                                                                   |
        | - Auto-saved to outputs/report.md                                                 |
        | - Corporate-styled PDF generated via fpdf2                                        |
        | - Full audit record, metadata, and markdown stored in SQLite Database             |
        +-----------------------------------------------------------------------------------+
        ```
        """
    )
