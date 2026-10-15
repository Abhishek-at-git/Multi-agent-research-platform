"""Settings and configuration management for Multi-Agent Research Assistant.

Loads environment variables, initializes Gemini LLM for CrewAI,
and configures logging and runtime paths.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Locate project roots and load .env from current directory or parent directories
CURRENT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = CURRENT_DIR.parent

dotenv_paths = [
    CURRENT_DIR / ".env",
    PROJECT_ROOT / ".env",
    Path(".env"),
]
for p in dotenv_paths:
    if p.exists():
        load_dotenv(dotenv_path=p, override=False)
        break
else:
    load_dotenv()  # Fallback to standard environment search


class Settings(BaseSettings):
    """Application settings with environment variable fallback and validation."""

    # Gemini API Configuration
    gemini_api_key: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", ""),
        description="Google Gemini API Key",
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini/gemini-3.8-flash"),
        description="Gemini Model Identifier for LiteLLM/CrewAI",
    )
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for Gemini LLM sampling (0.0 to 1.0)",
    )

    # Search Configuration
    search_max_results: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Maximum search results retrieved per search query",
    )
    search_timeout_seconds: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Timeout in seconds for web requests",
    )

    # Output & Persistence Directories
    base_dir: Path = Field(default=CURRENT_DIR)
    outputs_dir: Path = Field(default_factory=lambda: CURRENT_DIR / "outputs")
    reports_dir: Path = Field(default_factory=lambda: CURRENT_DIR / "outputs" / "reports")
    database_path: Path = Field(
        default_factory=lambda: CURRENT_DIR / "outputs" / "research_assistant.db"
    )

    # Logging
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    log_file: Path = Field(
        default_factory=lambda: CURRENT_DIR / "outputs" / "research.log"
    )

    # Localization
    default_language: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "English")
    )

    class Config:
        arbitrary_types_allowed = True
        extra = "ignore"


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve or initialize the singleton application settings."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        # Ensure outputs directory exists
        _settings_instance.outputs_dir.mkdir(parents=True, exist_ok=True)
        _settings_instance.reports_dir.mkdir(parents=True, exist_ok=True)
    return _settings_instance


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure structured, production-ready logging with console and file handlers."""
    settings = get_settings()
    log_level_str = level or settings.log_level
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger("research_assistant")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if re-called
    if logger.handlers:
        return logger

    # Formatting
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler (Rich if available, standard StreamHandler fallback)
    try:
        from rich.logging import RichHandler

        console_handler = RichHandler(
            level=log_level,
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
    except ImportError:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)

    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File Handler
    try:
        settings.outputs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    except Exception as exc:
        logger.warning(f"Could not attach file log handler: {exc}")

    return logger


LEGACY_MODEL_REPLACEMENTS = {
    "gemini/gemini-2.0-flash": "gemini/gemini-3.8-flash",
    "gemini/gemini-2.0-flash-exp": "gemini/gemini-3.8-flash",
    "gemini/gemini-1.5-flash": "gemini/gemini-3.8-flash",
    "gemini/gemini-1.5-pro": "gemini/gemini-3.8-flash",
    "gemini/gemini-2.5-flash": "gemini/gemini-3.8-flash",
    "gemini/gemini-2.5-pro": "gemini/gemini-3.8-flash",
    "gemini-2.0-flash": "gemini/gemini-3.8-flash",
    "gemini-2.0-flash-exp": "gemini/gemini-3.8-flash",
    "gemini-1.5-flash": "gemini/gemini-3.8-flash",
    "gemini-1.5-pro": "gemini/gemini-3.8-flash",
    "gemini-2.5-flash": "gemini/gemini-3.8-flash",
    "gemini-2.5-pro": "gemini/gemini-3.8-flash",
}


def normalize_gemini_model_name(model_name: str) -> str:
    """Ensure Gemini model name has the appropriate prefix and upgrade deprecated models."""
    cleaned = model_name.strip()
    # Check if a legacy model was requested and upgrade it
    if cleaned in LEGACY_MODEL_REPLACEMENTS:
        logging.getLogger("research_assistant").info(
            f"Upgrading deprecated model '{cleaned}' to '{LEGACY_MODEL_REPLACEMENTS[cleaned]}'"
        )
        return LEGACY_MODEL_REPLACEMENTS[cleaned]

    if cleaned.startswith("models/"):
        cleaned = cleaned.replace("models/", "")
    if not cleaned.startswith("gemini/"):
        cleaned = f"gemini/{cleaned}"

    # Check again with gemini/ prefix
    if cleaned in LEGACY_MODEL_REPLACEMENTS:
        return LEGACY_MODEL_REPLACEMENTS[cleaned]

    return cleaned


def get_gemini_llm(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None,
):
    """Instantiate and configure CrewAI LLM configured for Google Gemini.

    Args:
        model_name: Optional override for Gemini model.
        api_key: Optional override for Gemini API Key.
        temperature: Optional temperature parameter (default 0.3 for analytical precision).

    Returns:
        crewai.LLM: Initialized LLM instance.

    Raises:
        ValueError: If GEMINI_API_KEY is not configured.
    """
    from crewai import LLM

    settings = get_settings()
    key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")

    if not key or key.strip() in ("", "your_gemini_api_key_here"):
        raise ValueError(
            "GEMINI_API_KEY is missing or invalid! "
            "Please provide a valid Gemini API key in your .env file or pass it to get_gemini_llm()."
        )

    # Export to environment for LiteLLM / Google GenAI SDK compliance
    os.environ["GEMINI_API_KEY"] = key.strip()

    raw_model = model_name or settings.gemini_model
    final_model = normalize_gemini_model_name(raw_model)
    temp = temperature if temperature is not None else settings.llm_temperature

    return LLM(
        model=final_model,
        api_key=key.strip(),
        temperature=temp,
    )
