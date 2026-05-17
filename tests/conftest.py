"""Pytest hooks for the code-review-agent test suite."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _do_not_merge_developer_dotenv(monkeypatch):
    """Unit tests rely on patched os.environ, not ~/code_Agent/.env on disk."""
    import config as cfg_module

    monkeypatch.setattr(
        cfg_module,
        "_PROJECT_DOTENV_PATH",
        Path("/__pytest__/missing_code_agent_dotenv__/"),
    )
