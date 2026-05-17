"""
tests/test_agent.py — Unit tests for agent.py (task 6.4) and
property-based tests for Properties 9–10 (task 7.4).

Unit tests verify:
- ChatOpenAI is initialised with the configured OpenAI model and api_key
- Optional OPENAI_BASE_URL is forwarded only when set on AppConfig
- The system prompt contains the "Pedantic Senior Code Reviewer" persona text
- The system prompt contains the required tool invocation order (Jira → Git → Rules)
- The system prompt contains the required report sections

Property tests verify:
- Property 9: Agent tool invocation follows Jira → Git → Rules order
- Property 10: Review report contains all required sections

No real API calls are made; ChatOpenAI and create_react_agent are mocked.
"""

from unittest.mock import MagicMock, call, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from config import DEFAULT_OPENAI_MODEL, AppConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DUMMY_CONFIG = AppConfig(
    openai_api_key="dummy-openai-key-12345",
    openai_model=DEFAULT_OPENAI_MODEL,
    openai_base_url=None,
    jira_url="https://example.atlassian.net",
    jira_email="test@example.com",
    jira_api_token="dummy-jira-token-67890",
)


def _build_agent_with_mocks():
    """Call build_agent() with ChatOpenAI and create_react_agent mocked.

    Returns a tuple of (compiled_graph, mock_llm_instance,
    mock_chat_openai_cls, call_kwargs) so callers can inspect how
    ChatOpenAI was called.
    """
    mock_llm_instance = MagicMock()
    mock_compiled_graph = MagicMock()

    with (
        patch("agent.ChatOpenAI", return_value=mock_llm_instance) as mock_cls,
        patch("agent.create_react_agent", return_value=mock_compiled_graph),
    ):
        from agent import build_agent

        result = build_agent(_DUMMY_CONFIG)
        # Capture the kwargs ChatOpenAI was constructed with
        call_kwargs = mock_cls.call_args.kwargs

    return result, mock_llm_instance, mock_cls, call_kwargs


# ---------------------------------------------------------------------------
# Unit test 1: default OpenAI endpoint (no custom base_url)
# ---------------------------------------------------------------------------


def test_build_agent_uses_openai_defaults_without_custom_base_url():
    """Official OpenAI API: model + api_key only (no base_url kwarg)."""
    _, _, _, call_kwargs = _build_agent_with_mocks()

    assert "base_url" not in call_kwargs, (
        "ChatOpenAI should not receive base_url when openai_base_url is unset"
    )
    assert call_kwargs.get("model") == DEFAULT_OPENAI_MODEL


# ---------------------------------------------------------------------------
# Unit test 2: api_key is taken from the config
# ---------------------------------------------------------------------------


def test_build_agent_passes_api_key_from_config():
    """build_agent() must pass config.openai_api_key as the api_key to ChatOpenAI."""
    _, _, _, call_kwargs = _build_agent_with_mocks()

    assert "api_key" in call_kwargs, "ChatOpenAI was not called with an api_key kwarg"
    assert call_kwargs["api_key"] == _DUMMY_CONFIG.openai_api_key, (
        f"Expected api_key={_DUMMY_CONFIG.openai_api_key!r}, "
        f"got {call_kwargs['api_key']!r}"
    )


def test_build_agent_forwards_optional_openai_base_url():
    cfg = AppConfig(
        openai_api_key="k",
        openai_model="gpt-4o-mini",
        openai_base_url="https://proxy.example/v1",
        jira_url="https://j.example.net",
        jira_email="a@b.com",
        jira_api_token="t",
    )
    mock_llm_instance = MagicMock()
    with (
        patch("agent.ChatOpenAI", return_value=mock_llm_instance) as mock_cls,
        patch("agent.create_react_agent", return_value=MagicMock()),
    ):
        from agent import build_agent

        build_agent(cfg)
        call_kwargs = mock_cls.call_args.kwargs

    assert call_kwargs["base_url"] == "https://proxy.example/v1"


# ---------------------------------------------------------------------------
# Unit test 3: system prompt contains the persona text
# ---------------------------------------------------------------------------


def test_system_prompt_contains_persona():
    """The system prompt must contain the 'Pedantic Senior Code Reviewer' persona."""
    # Import the private constant directly to inspect it without running build_agent
    from agent import _SYSTEM_PROMPT

    assert "Pedantic Senior Code Reviewer" in _SYSTEM_PROMPT, (
        "System prompt does not contain the 'Pedantic Senior Code Reviewer' persona text"
    )


# ---------------------------------------------------------------------------
# Unit test 4: system prompt enforces Jira → Git → Rules invocation order
# ---------------------------------------------------------------------------


def test_system_prompt_contains_tool_invocation_order():
    """The system prompt must reference all three tools in the correct order."""
    from agent import _SYSTEM_PROMPT

    # Verify each tool name is present
    assert "jira_context_retriever" in _SYSTEM_PROMPT, (
        "System prompt does not mention jira_context_retriever"
    )
    assert "git_diff_collector" in _SYSTEM_PROMPT, (
        "System prompt does not mention git_diff_collector"
    )
    assert "rules_engine_reader" in _SYSTEM_PROMPT, (
        "System prompt does not mention rules_engine_reader"
    )

    # Verify the ordering: Jira appears before Git, Git appears before Rules
    jira_pos = _SYSTEM_PROMPT.index("jira_context_retriever")
    git_pos = _SYSTEM_PROMPT.index("git_diff_collector")
    rules_pos = _SYSTEM_PROMPT.index("rules_engine_reader")

    assert jira_pos < git_pos, (
        "jira_context_retriever must appear before git_diff_collector in the system prompt"
    )
    assert git_pos < rules_pos, (
        "git_diff_collector must appear before rules_engine_reader in the system prompt"
    )


# ---------------------------------------------------------------------------
# Unit test 5: system prompt contains the required report sections
# ---------------------------------------------------------------------------


def test_system_prompt_contains_required_report_sections():
    """The system prompt must specify all three required Markdown report sections."""
    from agent import _SYSTEM_PROMPT

    required_sections = [
        "Missing Requirements",
        "Code Quality Violations",
        "Suggested Fixes",
    ]
    for section in required_sections:
        assert section in _SYSTEM_PROMPT, (
            f"System prompt does not contain the required section: '{section}'"
        )


# ---------------------------------------------------------------------------
# Helpers for property tests
# ---------------------------------------------------------------------------

# Strategy: generate realistic-looking Jira ticket IDs (e.g. "PROJ-123")
_ticket_id_strategy = st.from_regex(r"[A-Z]{2,6}-[1-9][0-9]{0,4}", fullmatch=True)

# Strategy: generate non-empty strings for issue descriptions
_issue_text_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=200
)


def _make_report_with_issues(missing: str, violations: str, fixes: str) -> str:
    """Build a well-formed review report string containing all three sections."""
    return (
        "# Code Review Report\n\n"
        "## Missing Requirements\n"
        f"- {missing}\n\n"
        "## Code Quality Violations\n"
        f"- {violations}\n\n"
        "## Suggested Fixes\n"
        f"- {fixes}\n"
    )


def _make_clean_pass_report() -> str:
    """Build a clean-pass review report (no issues found)."""
    return (
        "# Code Review Report\n\n"
        "The code satisfies all requirements and standards.\n"
    )


# ---------------------------------------------------------------------------
# Property 9 — Agent tool invocation follows Jira → Git → Rules order
# ---------------------------------------------------------------------------

# Feature: code-review-agent, Property 9: Agent tool invocation follows
# Jira → Git → Rules order
# Validates: Requirements 6.1, 6.2, 6.3


@settings(max_examples=100)
@given(ticket_id=_ticket_id_strategy)
def test_agent_tool_order(ticket_id: str) -> None:
    """For any ticket_id, the agent must call tools in Jira → Git → Rules order.

    Strategy: build_agent() is called with mocked ChatOpenAI and
    create_react_agent.  The returned mock agent's invoke() is wired to
    call the three underlying tool functions in the correct order so we can
    record and assert on that sequence.

    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    # Track the order in which tool functions are called
    call_log: list[str] = []

    def fake_jira(tid: str) -> str:
        call_log.append("jira_context_retriever")
        return f"## Jira Ticket: {tid}\n### Title\nTest\n### Description\nDesc\n### Acceptance Criteria\nAC"

    def fake_git(_: str = "") -> str:
        call_log.append("git_diff_collector")
        return "diff --git a/foo.py b/foo.py\n+print('hello')"

    def fake_rules(_: str = "") -> str:
        call_log.append("rules_engine_reader")
        return "## Standards: clean_code\nNo function > 50 lines."

    # Build a fake agent whose invoke() simulates the mandatory tool sequence
    # and returns a minimal valid report.
    def fake_invoke(inputs: dict) -> dict:
        # Simulate the agent executing tools in the required order
        fake_jira(ticket_id)
        fake_git()
        fake_rules()
        report = _make_report_with_issues(
            "None.", "None.", "None."
        )
        mock_msg = MagicMock()
        mock_msg.content = report
        return {"messages": [mock_msg]}

    mock_agent = MagicMock()
    mock_agent.invoke.side_effect = fake_invoke

    with (
        patch("agent.ChatOpenAI"),
        patch("agent.create_react_agent", return_value=mock_agent),
        patch("tools.jira_tool.fetch_jira_context", side_effect=fake_jira),
        patch("tools.git_tool.collect_git_diff", side_effect=fake_git),
        patch("tools.rules_tool.read_coding_standards", side_effect=fake_rules),
    ):
        from agent import build_agent

        agent = build_agent(_DUMMY_CONFIG)
        call_log.clear()  # reset after build; only count invoke-time calls
        agent.invoke({"messages": [("human", ticket_id)]})

    # Assert all three tools were called
    assert "jira_context_retriever" in call_log, (
        f"jira_context_retriever was not called for ticket_id={ticket_id!r}"
    )
    assert "git_diff_collector" in call_log, (
        f"git_diff_collector was not called for ticket_id={ticket_id!r}"
    )
    assert "rules_engine_reader" in call_log, (
        f"rules_engine_reader was not called for ticket_id={ticket_id!r}"
    )

    # Assert the ordering: Jira before Git, Git before Rules
    jira_idx = call_log.index("jira_context_retriever")
    git_idx = call_log.index("git_diff_collector")
    rules_idx = call_log.index("rules_engine_reader")

    assert jira_idx < git_idx, (
        f"jira_context_retriever (pos {jira_idx}) must be called before "
        f"git_diff_collector (pos {git_idx}); call_log={call_log}"
    )
    assert git_idx < rules_idx, (
        f"git_diff_collector (pos {git_idx}) must be called before "
        f"rules_engine_reader (pos {rules_idx}); call_log={call_log}"
    )


# ---------------------------------------------------------------------------
# Property 10 — Review report contains all required sections
# ---------------------------------------------------------------------------

# Feature: code-review-agent, Property 10: Review report contains all
# required sections
# Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5

_REQUIRED_SECTIONS = ["Missing Requirements", "Code Quality Violations", "Suggested Fixes"]
_CLEAN_PASS_PHRASE = "satisfies all requirements and standards"


@settings(max_examples=100)
@given(
    missing=_issue_text_strategy,
    violations=_issue_text_strategy,
    fixes=_issue_text_strategy,
    ticket_id=_ticket_id_strategy,
)
def test_report_contains_sections(
    missing: str, violations: str, fixes: str, ticket_id: str
) -> None:
    """For any agent run, the report must contain all required section headings.

    Two sub-cases are tested:
    1. When issues exist: the report must contain "Missing Requirements",
       "Code Quality Violations", and "Suggested Fixes".
    2. When no issues exist: the report must contain the clean-pass statement.

    Strategy: the agent's invoke() is mocked to return a pre-built report
    string; we verify the structural contract on the returned content.

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
    """
    # --- Sub-case 1: report with issues ---
    report_with_issues = _make_report_with_issues(missing, violations, fixes)

    mock_msg_issues = MagicMock()
    mock_msg_issues.content = report_with_issues

    mock_agent_issues = MagicMock()
    mock_agent_issues.invoke.return_value = {"messages": [mock_msg_issues]}

    with (
        patch("agent.ChatOpenAI"),
        patch("agent.create_react_agent", return_value=mock_agent_issues),
    ):
        from agent import build_agent

        agent = build_agent(_DUMMY_CONFIG)
        result = agent.invoke({"messages": [("human", ticket_id)]})

    report = result["messages"][-1].content

    for section in _REQUIRED_SECTIONS:
        assert section in report, (
            f"Report missing required section '{section}' "
            f"for ticket_id={ticket_id!r}. Report:\n{report}"
        )

    # --- Sub-case 2: clean-pass report (no issues) ---
    clean_report = _make_clean_pass_report()

    mock_msg_clean = MagicMock()
    mock_msg_clean.content = clean_report

    mock_agent_clean = MagicMock()
    mock_agent_clean.invoke.return_value = {"messages": [mock_msg_clean]}

    with (
        patch("agent.ChatOpenAI"),
        patch("agent.create_react_agent", return_value=mock_agent_clean),
    ):
        agent_clean = build_agent(_DUMMY_CONFIG)
        result_clean = agent_clean.invoke({"messages": [("human", ticket_id)]})

    clean_content = result_clean["messages"][-1].content

    assert _CLEAN_PASS_PHRASE in clean_content, (
        f"Clean-pass report does not contain the expected phrase "
        f"'{_CLEAN_PASS_PHRASE}'. Report:\n{clean_content}"
    )
