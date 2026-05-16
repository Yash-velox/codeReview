"""
config.py — Environment Configuration Module

Loads and validates all required environment variables from a .env file
using python-dotenv, then returns them as a typed AppConfig dataclass.

Secrets (XAI_API_KEY, JIRA_API_TOKEN) are never written to logs.
"""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Module-level logger — all output goes through this, never raw print()
logger = logging.getLogger(__name__)

# The four required environment variable names
_REQUIRED_VARS = ("XAI_API_KEY", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")

# Variables whose values must never appear in log output
_SECRET_VARS = frozenset({"XAI_API_KEY", "JIRA_API_TOKEN"})


@dataclass
class AppConfig:
    """Typed container for all required runtime configuration values."""

    xai_api_key: str      # XAI_API_KEY — never logged
    jira_url: str         # JIRA_URL
    jira_email: str       # JIRA_EMAIL
    jira_api_token: str   # JIRA_API_TOKEN — never logged


def load_config() -> AppConfig:
    """Load and validate required environment variables from a .env file.

    Reads the .env file (if present) into the process environment via
    python-dotenv, then checks that every required variable is set.

    Returns:
        AppConfig: Dataclass populated with the four required values.

    Raises:
        EnvironmentError: If any required variable is absent from the
            environment after loading .env.  The error message names the
            missing variable explicitly.
    """
    # Load .env into os.environ; override=False keeps existing env vars intact
    load_dotenv(override=False)
    logger.debug("Attempted to load .env file into environment.")

    # Collect values, raising immediately on the first missing variable
    resolved: dict[str, str] = {}
    for var in _REQUIRED_VARS:
        value = os.environ.get(var)
        if not value:
            # Name the missing variable in the error so the caller knows
            # exactly what to fix — never log a secret value here
            raise EnvironmentError(
                f"Required environment variable '{var}' is missing or empty. "
                "Check your .env file or shell environment."
            )
        resolved[var] = value

    # Log only non-secret variable names/values to confirm successful load
    for var, value in resolved.items():
        if var in _SECRET_VARS:
            # Acknowledge the secret is present without revealing its value
            logger.debug("Loaded secret variable '%s': [REDACTED]", var)
        else:
            logger.debug("Loaded variable '%s': %s", var, value)

    logger.info(
        "Configuration loaded successfully. Variables present: %s",
        ", ".join(_REQUIRED_VARS),
    )

    # Construct and return the typed config dataclass
    return AppConfig(
        xai_api_key=resolved["XAI_API_KEY"],
        jira_url=resolved["JIRA_URL"],
        jira_email=resolved["JIRA_EMAIL"],
        jira_api_token=resolved["JIRA_API_TOKEN"],
    )
