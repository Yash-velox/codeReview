"""
config.py — Environment Configuration Module

Loads and validates required environment variables from a .env file using
python-dotenv, then returns them as a typed AppConfig dataclass.

Secrets (OPENAI_API_KEY, JIRA_API_TOKEN) are never written to logs.
"""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Required env vars (must be non-empty strings)
_REQUIRED_VARS = ("OPENAI_API_KEY", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")

_SECRET_VARS = frozenset({"OPENAI_API_KEY", "JIRA_API_TOKEN"})

# Default chat model — small/cheap; override with OPENAI_MODEL if needed.
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass
class AppConfig:
    """Typed container for all runtime configuration values."""

    openai_api_key: str       # OPENAI_API_KEY — never logged
    openai_model: str         # OPENAI_MODEL or DEFAULT_OPENAI_MODEL
    openai_base_url: str | None  # OPENAI_BASE_URL when set (otherwise official API)
    jira_url: str             # JIRA_URL
    jira_email: str           # JIRA_EMAIL
    jira_api_token: str       # JIRA_API_TOKEN — never logged


def load_config() -> AppConfig:
    """Load and validate environment variables from a .env file.

    OPENAI_MODEL and OPENAI_BASE_URL are optional:
    - OPENAI_MODEL defaults to ``gpt-4o-mini`` when unset or blank.
    - OPENAI_BASE_URL: leave unset for ``https://api.openai.com/v1`` (ChatOpenAI default).

    Returns:
        AppConfig populated with all values.

    Raises:
        EnvironmentError: If any required variable is missing or empty.
    """
    load_dotenv(override=False)
    logger.debug("Attempted to load .env file into environment.")

    resolved: dict[str, str] = {}
    for var in _REQUIRED_VARS:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Required environment variable '{var}' is missing or empty. "
                "Check your .env file or shell environment."
            )
        resolved[var] = value

    model_raw = os.environ.get("OPENAI_MODEL", "").strip()
    openai_model = model_raw if model_raw else DEFAULT_OPENAI_MODEL

    base_raw = os.environ.get("OPENAI_BASE_URL", "").strip()
    openai_base_url = base_raw if base_raw else None

    for var, value in resolved.items():
        if var in _SECRET_VARS:
            logger.debug("Loaded secret variable '%s': [REDACTED]", var)
        else:
            logger.debug("Loaded variable '%s': %s", var, value)

    logger.debug(
        "OpenAI model=%s base_url=%s",
        openai_model,
        "[custom]" if openai_base_url else "[default]",
    )

    logger.info(
        "Configuration loaded successfully. Variables present: %s",
        ", ".join(_REQUIRED_VARS),
    )

    return AppConfig(
        openai_api_key=resolved["OPENAI_API_KEY"],
        openai_model=openai_model,
        openai_base_url=openai_base_url,
        jira_url=resolved["JIRA_URL"],
        jira_email=resolved["JIRA_EMAIL"],
        jira_api_token=resolved["JIRA_API_TOKEN"],
    )
