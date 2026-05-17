"""
tests/test_config.py — Property-based and unit tests for config.py

Tests Properties 1–3 from the design document using Hypothesis.
"""

import logging
import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from config import DEFAULT_GROQ_MODEL, AppConfig, load_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_VARS = ("GROQ_API_KEY", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")

_nonempty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=64,
)

_secret_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        blacklist_characters="\x00",
    ),
    min_size=16,
    max_size=64,
)


def _norm_secret(raw: str) -> str:
    """Mirror config sanitization for GROQ_API_KEY / JIRA_API_TOKEN."""
    return raw.strip().strip('"').strip("'")


def _norm_plain(raw: str) -> str:
    """Mirror config sanitization for URL/email-style values."""
    return raw.strip()


def _env_dict(**overrides: str) -> dict[str, str]:
    base = {
        "GROQ_API_KEY": "key",
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "token",
    }
    base.update(overrides)
    return base


def test_load_config_with_full_env():
    env = {
        "GROQ_API_KEY": "test-groq-key",
        "JIRA_URL": "https://myorg.atlassian.net",
        "JIRA_EMAIL": "dev@myorg.com",
        "JIRA_API_TOKEN": "jira-secret-token",
    }
    with patch.dict(os.environ, env, clear=True):
        config = load_config()

    assert isinstance(config, AppConfig)
    assert config.groq_api_key == "test-groq-key"
    assert config.groq_model == DEFAULT_GROQ_MODEL
    assert config.jira_url == "https://myorg.atlassian.net"
    assert config.jira_email == "dev@myorg.com"
    assert config.jira_api_token == "jira-secret-token"


def test_load_config_groq_model_override():
    env = _env_dict(GROQ_MODEL="llama-3.1-8b-instant")
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.groq_model == "llama-3.1-8b-instant"


@given(
    groq_api_key=_nonempty_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_nonempty_text,
)
@settings(max_examples=100)
def test_config_loads_all_keys(
    groq_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    from hypothesis import assume

    assume(_norm_secret(groq_api_key) != "")
    assume(_norm_plain(jira_url) != "")
    assume(_norm_plain(jira_email) != "")
    assume(_norm_secret(jira_api_token) != "")

    env = {
        "GROQ_API_KEY": groq_api_key,
        "JIRA_URL": jira_url,
        "JIRA_EMAIL": jira_email,
        "JIRA_API_TOKEN": jira_api_token,
    }
    with patch.dict(os.environ, env, clear=True):
        config = load_config()

    assert isinstance(config, AppConfig)
    assert config.groq_api_key == _norm_secret(groq_api_key)
    assert config.groq_model == DEFAULT_GROQ_MODEL
    assert config.jira_url == _norm_plain(jira_url)
    assert config.jira_email == _norm_plain(jira_email)
    assert config.jira_api_token == _norm_secret(jira_api_token)


@given(
    missing_vars=st.frozensets(
        st.sampled_from(list(_REQUIRED_VARS)),
        min_size=1,
    ),
    groq_api_key=_nonempty_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_nonempty_text,
)
@settings(max_examples=100)
def test_missing_var_raises(
    missing_vars: frozenset,
    groq_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    full_env = {
        "GROQ_API_KEY": groq_api_key,
        "JIRA_URL": jira_url,
        "JIRA_EMAIL": jira_email,
        "JIRA_API_TOKEN": jira_api_token,
    }
    partial_env = {k: v for k, v in full_env.items() if k not in missing_vars}

    with patch("config.load_dotenv"):
        with patch.dict(os.environ, partial_env, clear=True):
            with pytest.raises(EnvironmentError) as exc_info:
                load_config()

    error_message = str(exc_info.value)
    assert any(var in error_message for var in missing_vars), (
        f"EnvironmentError message {error_message!r} does not name any of "
        f"the missing variables: {missing_vars}"
    )


@given(
    groq_api_key=_secret_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_secret_text,
)
@settings(max_examples=100)
def test_secrets_not_in_logs(
    groq_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    from hypothesis import assume

    assume(groq_api_key not in jira_url)
    assume(groq_api_key not in jira_email)
    assume(jira_api_token not in jira_url)
    assume(jira_api_token not in jira_email)
    assume(groq_api_key not in jira_api_token)
    assume(jira_api_token not in groq_api_key)
    assume(_norm_plain(jira_url) != "")
    assume(_norm_plain(jira_email) != "")
    env = {
        "GROQ_API_KEY": groq_api_key,
        "JIRA_URL": jira_url,
        "JIRA_EMAIL": jira_email,
        "JIRA_API_TOKEN": jira_api_token,
    }

    log_records: list[str] = []

    class _CapturingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(self.format(record))

    handler = _CapturingHandler()
    handler.setLevel(logging.DEBUG)
    config_logger = logging.getLogger("config")
    config_logger.addHandler(handler)
    original_level = config_logger.level
    config_logger.setLevel(logging.DEBUG)

    try:
        with patch.dict(os.environ, env, clear=True):
            load_config()
    finally:
        config_logger.removeHandler(handler)
        config_logger.setLevel(original_level)

    combined_log_output = "\n".join(log_records)

    assert groq_api_key not in combined_log_output, (
        "Secret GROQ_API_KEY value appeared in log output"
    )
    assert jira_api_token not in combined_log_output, (
        "Secret JIRA_API_TOKEN value appeared in log output"
    )
