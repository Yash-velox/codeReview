"""
tests/test_jira_tool.py — Property-based tests for tools/jira_tool.py

Tests Properties 4–5 from the design document using Hypothesis.
"""

import os
from unittest.mock import MagicMock, patch

import requests.exceptions
from hypothesis import given, settings
from hypothesis import strategies as st

from tools.jira_tool import fetch_jira_context

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty printable text (no null bytes)
_nonempty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=128,
)

# Valid-looking Jira ticket IDs (e.g. "PROJ-123")
_ticket_id = st.from_regex(r"[A-Z]{2,10}-[1-9][0-9]{0,4}", fullmatch=True)

# Strategy for a mocked Jira issue dict with all three required fields
_jira_issue = st.fixed_dictionaries(
    {
        "fields": st.fixed_dictionaries(
            {
                "summary": _nonempty_text,
                "description": _nonempty_text,
                "customfield_10016": _nonempty_text,
            }
        )
    }
)

# Env vars required by fetch_jira_context
_JIRA_ENV = {
    "JIRA_URL": "https://example.atlassian.net",
    "JIRA_EMAIL": "user@example.com",
    "JIRA_API_TOKEN": "test-token",
}


# ---------------------------------------------------------------------------
# Property 4: Jira retrieval returns all required fields
# ---------------------------------------------------------------------------


@given(ticket_id=_ticket_id, issue=_jira_issue)
@settings(max_examples=100)
def test_jira_returns_all_fields(ticket_id: str, issue: dict) -> None:
    # Feature: code-review-agent, Property 4: Jira retrieval returns all required fields
    # Validates: Requirements 2.1, 2.2
    #
    # For any valid ticket_id and any mocked Jira ticket with a title,
    # description, and acceptance criteria, fetch_jira_context() must return
    # a string that contains all three field values.

    fields = issue["fields"]
    title = fields["summary"]
    description = fields["description"]
    acceptance_criteria = fields["customfield_10016"]

    mock_jira_instance = MagicMock()
    mock_jira_instance.get_issue.return_value = issue

    with patch.dict(os.environ, _JIRA_ENV, clear=True):
        with patch("tools.jira_tool.Jira", return_value=mock_jira_instance):
            result = fetch_jira_context(ticket_id)

    assert isinstance(result, str), "fetch_jira_context must return a string"
    assert title in result, f"Title {title!r} not found in result"
    assert description in result, f"Description {description!r} not found in result"
    assert acceptance_criteria in result, (
        f"Acceptance criteria {acceptance_criteria!r} not found in result"
    )


# ---------------------------------------------------------------------------
# Property 5: Invalid or unreachable Jira returns error string, no exception
# ---------------------------------------------------------------------------


@given(ticket_id=_ticket_id)
@settings(max_examples=100)
def test_jira_missing_ticket_returns_string(ticket_id: str) -> None:
    # Feature: code-review-agent, Property 5: Invalid or unreachable Jira returns error string, no exception
    # Validates: Requirements 2.3
    #
    # When the ticket does not exist (404), fetch_jira_context() must return
    # a non-empty string and must not raise an exception.

    mock_jira_instance = MagicMock()
    mock_jira_instance.get_issue.side_effect = Exception(
        f"404: Issue Does Not Exist for {ticket_id}"
    )

    with patch.dict(os.environ, _JIRA_ENV, clear=True):
        with patch("tools.jira_tool.Jira", return_value=mock_jira_instance):
            result = fetch_jira_context(ticket_id)

    assert isinstance(result, str), "fetch_jira_context must return a string on 404"
    assert len(result) > 0, "Returned error string must be non-empty"


@given(ticket_id=_ticket_id)
@settings(max_examples=100)
def test_jira_connectivity_failure_returns_string(ticket_id: str) -> None:
    # Feature: code-review-agent, Property 5: Invalid or unreachable Jira returns error string, no exception
    # Validates: Requirements 2.4
    #
    # When the Jira API is unreachable (ConnectionError), fetch_jira_context()
    # must return a non-empty string and must not raise an exception.

    mock_jira_instance = MagicMock()
    mock_jira_instance.get_issue.side_effect = requests.exceptions.ConnectionError(
        "Failed to establish a new connection"
    )

    with patch.dict(os.environ, _JIRA_ENV, clear=True):
        with patch("tools.jira_tool.Jira", return_value=mock_jira_instance):
            result = fetch_jira_context(ticket_id)

    assert isinstance(result, str), (
        "fetch_jira_context must return a string on ConnectionError"
    )
    assert len(result) > 0, "Returned error string must be non-empty"
