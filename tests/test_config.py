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

from config import DEFAULT_OPENAI_MODEL, AppConfig, load_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED_VARS = ("OPENAI_API_KEY", "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")

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


def _env_dict(**overrides: str) -> dict[str, str]:
    """Return a base env dict with all four vars set, applying any overrides."""
    base = {
        "OPENAI_API_KEY": "key",
        "JIRA_URL": "https://example.atlassian.net",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "token",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Unit test — fully populated environment
# ---------------------------------------------------------------------------


def test_load_config_with_full_env():
    """Unit test: load_config() succeeds when all four vars are present."""
    env = {
        "OPENAI_API_KEY": "test-openai-key",
        "JIRA_URL": "https://myorg.atlassian.net",
        "JIRA_EMAIL": "dev@myorg.com",
        "JIRA_API_TOKEN": "jira-secret-token",
    }
    with patch.dict(os.environ, env, clear=True):
        config = load_config()

    assert isinstance(config, AppConfig)
    assert config.openai_api_key == "test-openai-key"
    assert config.openai_model == DEFAULT_OPENAI_MODEL
    assert config.openai_base_url is None
    assert config.jira_url == "https://myorg.atlassian.net"
    assert config.jira_email == "dev@myorg.com"
    assert config.jira_api_token == "jira-secret-token"


def test_load_config_openai_model_override():
    env = _env_dict(OPENAI_MODEL="gpt-4o")
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.openai_model == "gpt-4o"


def test_load_config_openai_base_url_optional():
    env = _env_dict(OPENAI_BASE_URL="https://example.invalid/v1")
    with patch.dict(os.environ, env, clear=True):
        config = load_config()
    assert config.openai_base_url == "https://example.invalid/v1"


# ---------------------------------------------------------------------------
# Property 1: Config loads all required keys
# ---------------------------------------------------------------------------


@given(
    openai_api_key=_nonempty_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_nonempty_text,
)
@settings(max_examples=100)
def test_config_loads_all_keys(
    openai_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    env = {
        "OPENAI_API_KEY": openai_api_key,
        "JIRA_URL": jira_url,
        "JIRA_EMAIL": jira_email,
        "JIRA_API_TOKEN": jira_api_token,
    }
    with patch.dict(os.environ, env, clear=True):
        config = load_config()

    assert isinstance(config, AppConfig)
    assert config.openai_api_key == openai_api_key
    assert config.openai_model == DEFAULT_OPENAI_MODEL
    assert config.openai_base_url is None
    assert config.jira_url == jira_url
    assert config.jira_email == jira_email
    assert config.jira_api_token == jira_api_token


# ---------------------------------------------------------------------------
# Property 2: Missing env var raises EnvironmentError
# ---------------------------------------------------------------------------


@given(
    missing_vars=st.frozensets(
        st.sampled_from(list(_REQUIRED_VARS)),
        min_size=1,
    ),
    openai_api_key=_nonempty_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_nonempty_text,
)
@settings(max_examples=100)
def test_missing_var_raises(
    missing_vars: frozenset,
    openai_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    full_env = {
        "OPENAI_API_KEY": openai_api_key,
        "JIRA_URL": jira_url,
        "JIRA_EMAIL": jira_email,
        "JIRA_API_TOKEN": jira_api_token,
    }
    partial_env = {k: v for k, v in full_env.items() if k not in missing_vars}

    with patch.dict(os.environ, partial_env, clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            load_config()

    error_message = str(exc_info.value)
    assert any(var in error_message for var in missing_vars), (
        f"EnvironmentError message {error_message!r} does not name any of "
        f"the missing variables: {missing_vars}"
    )


# ---------------------------------------------------------------------------
# Property 3: Secrets never appear in log output
# ---------------------------------------------------------------------------


@given(
    openai_api_key=_secret_text,
    jira_url=_nonempty_text,
    jira_email=_nonempty_text,
    jira_api_token=_secret_text,
)
@settings(max_examples=100)
def test_secrets_not_in_logs(
    openai_api_key: str,
    jira_url: str,
    jira_email: str,
    jira_api_token: str,
) -> None:
    from hypothesis import assume

    assume(openai_api_key not in jira_url)
    assume(openai_api_key not in jira_email)
    assume(jira_api_token not in jira_url)
    assume(jira_api_token not in jira_email)
    assume(openai_api_key not in jira_api_token)
    assume(jira_api_token not in openai_api_key)
    env = {
        "OPENAI_API_KEY": openai_api_key,
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

    assert openai_api_key not in combined_log_output, (
        "Secret OPENAI_API_KEY value appeared in log output"
    )
    assert jira_api_token not in combined_log_output, (
        "Secret JIRA_API_TOKEN value appeared in log output"
    )
