"""
tools/jira_tool.py — JiraContextRetriever

Fetches Jira ticket metadata (title, description, acceptance criteria) using
the atlassian-python-api library and exposes the function as a LangChain Tool.

Credentials are read directly from os.environ; load_config() must be called
before this tool is invoked so that the variables are present.
"""

import os

import requests.exceptions
from atlassian import Jira
from langchain_core.tools import Tool

# ---------------------------------------------------------------------------
# Core retrieval function
# ---------------------------------------------------------------------------


def fetch_jira_context(ticket_id: str) -> str:
    """Connect to Jira and return a structured context string for *ticket_id*.

    Reads JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN from the environment.
    On success returns a Markdown-formatted string with the ticket's title,
    description, and acceptance criteria.  On failure returns a descriptive
    error string — no exception is ever raised to the caller.

    Args:
        ticket_id: A Jira issue key, e.g. ``"PROJ-123"``.

    Returns:
        A structured string on success, or a descriptive error string on
        failure (missing ticket, connectivity problem, etc.).
    """
    # --- Read credentials from environment (populated by load_config()) ---
    jira_url = os.environ.get("JIRA_URL", "")
    jira_email = os.environ.get("JIRA_EMAIL", "")
    jira_api_token = os.environ.get("JIRA_API_TOKEN", "")

    if not all([jira_url, jira_email, jira_api_token]):
        return (
            "Error: One or more Jira credentials are missing from the environment "
            "(JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN). "
            "Ensure load_config() has been called before using this tool."
        )

    try:
        # --- Initialise the Jira Cloud client ---
        jira = Jira(
            url=jira_url,
            username=jira_email,
            password=jira_api_token,
            cloud=True,
        )

        # --- Fetch the issue; raises an exception on 404 or network error ---
        issue = jira.get_issue(ticket_id)

        return _format_ticket(ticket_id, issue)

    except requests.exceptions.ConnectionError as exc:
        # Network-level failure (DNS, timeout, refused connection, etc.)
        return (
            f"Error: Unable to reach the Jira API at '{jira_url}'. "
            f"Check your network connection and JIRA_URL. Details: {exc}"
        )
    except Exception as exc:  # noqa: BLE001
        # Covers 404 (issue not found), auth failures, and any other error
        error_text = str(exc)
        if "404" in error_text or "Issue Does Not Exist" in error_text:
            return (
                f"Error: Jira ticket '{ticket_id}' was not found. "
                "Verify the ticket ID and that you have permission to view it."
            )
        return (
            f"Error: Failed to retrieve Jira ticket '{ticket_id}'. "
            f"Details: {exc}"
        )


# ---------------------------------------------------------------------------
# Internal helper — kept separate to stay within the 50-line function limit
# ---------------------------------------------------------------------------


def _format_ticket(ticket_id: str, issue: dict) -> str:
    """Build the structured context string from a raw Jira issue dict.

    Args:
        ticket_id: The original ticket key used in the request.
        issue: The dict returned by ``Jira.get_issue()``.

    Returns:
        A Markdown-formatted string with title, description, and acceptance
        criteria sections.
    """
    # Navigate the nested 'fields' dict returned by atlassian-python-api
    fields = issue.get("fields", {})

    # --- Extract the three required fields ---
    title = fields.get("summary") or "(no title)"
    description = fields.get("description") or "(no description)"

    # Acceptance criteria live in a custom field; try the most common names.
    # customfield_10016 is the default Story Points / Acceptance Criteria field
    # in many Jira Cloud configurations.  Fall back gracefully if absent.
    acceptance_criteria = (
        fields.get("customfield_10016")
        or fields.get("customfield_10014")
        or fields.get("acceptance_criteria")
        or "(no acceptance criteria found)"
    )

    # --- Assemble the structured output string ---
    return (
        f"## Jira Ticket: {ticket_id}\n"
        f"### Title\n{title}\n"
        f"### Description\n{description}\n"
        f"### Acceptance Criteria\n{acceptance_criteria}"
    )


# ---------------------------------------------------------------------------
# LangChain Tool registration
# ---------------------------------------------------------------------------

# Expose fetch_jira_context as a named LangChain Tool so the ReAct agent can
# discover and invoke it by name during its reasoning loop.
jira_context_retriever = Tool(
    name="jira_context_retriever",
    func=fetch_jira_context,
    description=(
        "Fetches the title, description, and acceptance criteria for a Jira ticket. "
        "Input must be a Jira issue key string (e.g. 'PROJ-123'). "
        "Returns a structured Markdown string on success, or a descriptive error "
        "string if the ticket does not exist or the Jira API is unreachable."
    ),
)
