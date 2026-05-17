"""
config.py — Environment Configuration Module

Loads and validates required environment variables from a .env file
using python-dotenv, then returns them as a typed AppConfig dataclass.

Secrets (GROQ_API_KEY, JIRA_API_TOKEN) are never written to logs.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_PROJECT_DOTENV_PATH = Path(__file__).resolve().parent / ".env"

_REQUIRED_VARS = ("GROQ_API_KEY", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")

_SECRET_VARS = frozenset({"GROQ_API_KEY", "JIRA_API_TOKEN"})

# Groq OpenAI-compatible chat (see https://docs.groq.com/api-reference/openai-compatible )
DEFAULT_GROQ_API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


@dataclass
class AppConfig:
    """Typed container for all required runtime configuration values."""

    groq_api_key: str        # GROQ_API_KEY — never logged
    groq_model: str          # GROQ_MODEL or DEFAULT_GROQ_MODEL
    groq_api_base: str       # GROQ_API_BASE or DEFAULT_GROQ_API_BASE
    jira_url: str
    jira_email: str
    jira_api_token: str      # JIRA_API_TOKEN — never logged


def load_config() -> AppConfig:
    """Load and validate environment variables from ``code_Agent/.env``.

    Always loads **this package's** ``.env`` (next to ``config.py``), not a
    ``.env`` discovered from ``os.getcwd()``.

    Entries in that file overwrite existing ``os.environ`` values for keys
    defined in the file (``override=True`` in ``load_dotenv``).

    Returns:
        AppConfig populated with all values.

    Raises:
        EnvironmentError: If any required variable is missing or empty.
    """
    dotenv_loaded = load_dotenv(
        dotenv_path=_PROJECT_DOTENV_PATH,
        override=True,
    )
    logger.debug(
        "Loaded dotenv from %s loaded=%s (override=True)",
        _PROJECT_DOTENV_PATH,
        dotenv_loaded,
    )

    for _var in ("GROQ_API_KEY", "JIRA_API_TOKEN"):
        _rv = os.environ.get(_var)
        if _rv is not None:
            os.environ[_var] = _rv.strip().strip('"').strip("'")
    for _var in ("JIRA_URL", "JIRA_EMAIL"):
        _rv = os.environ.get(_var)
        if _rv:
            os.environ[_var] = _rv.strip()

    resolved: dict[str, str] = {}
    for var in _REQUIRED_VARS:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Required environment variable '{var}' is missing or empty. "
                "Check your .env file or shell environment."
            )
        resolved[var] = value

    for var, value in resolved.items():
        if var in _SECRET_VARS:
            logger.debug("Loaded secret variable '%s': [REDACTED]", var)
        else:
            logger.debug("Loaded variable '%s': %s", var, value)

    logger.info(
        "Configuration loaded successfully. Variables present: %s",
        ", ".join(_REQUIRED_VARS),
    )

    groq_model_raw = os.environ.get("GROQ_MODEL", "").strip()
    groq_model = groq_model_raw if groq_model_raw else DEFAULT_GROQ_MODEL

    groq_base_raw = os.environ.get("GROQ_API_BASE", "").strip().rstrip("/")
    groq_api_base = groq_base_raw if groq_base_raw else DEFAULT_GROQ_API_BASE

    return AppConfig(
        groq_api_key=resolved["GROQ_API_KEY"],
        groq_model=groq_model,
        groq_api_base=groq_api_base,
        jira_url=resolved["JIRA_URL"],
        jira_email=resolved["JIRA_EMAIL"],
        jira_api_token=resolved["JIRA_API_TOKEN"],
    )
