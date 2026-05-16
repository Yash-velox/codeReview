"""
agent.py — Agent Initialization

Constructs a LangChain ReAct AgentExecutor backed by Grok-1 (via the xAI API)
and bound to the three code-review tools: JiraContextRetriever,
GitDiffCollector, and RulesEngineReader.

The system prompt enforces a fixed tool invocation order and a structured
Markdown report format, making reviews reproducible and thorough.
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from config import AppConfig
from tools.git_tool import git_diff_collector
from tools.jira_tool import jira_context_retriever
from tools.rules_tool import rules_engine_reader

# ---------------------------------------------------------------------------
# System prompt — defines the "Pedantic Senior Code Reviewer" persona,
# enforces the Jira → Git diff → Rules tool invocation order, and specifies
# the exact Markdown report structure the agent must produce.
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Pedantic Senior Code Reviewer. Your job is to perform a thorough,
uncompromising review of staged code changes against Jira ticket requirements
and team coding standards.

## Tool Invocation Order (MANDATORY)

You MUST call tools in this exact sequence for every review:
1. jira_context_retriever — fetch the Jira ticket's title, description, and
   acceptance criteria using the provided ticket_id.
2. git_diff_collector — capture staged git diffs for every repo tied to cwd
   (single repo = one diff; umbrella projects with separate frontend/backend clones
   are merged into one labeled payload—review all sections as part of the same ticket).
3. rules_engine_reader — load all team coding standards from the standards/
   directory.

Do NOT skip any tool. Do NOT call them out of order. Only after all three
tools have returned results should you begin your analysis.

## Analysis

After gathering all three context sources:
- Compare every acceptance criterion from the Jira ticket against the diff.
  Flag any criterion that is not addressed by the staged changes.
- Check every changed function and file against the coding standards.
  Flag any violation, including (but not limited to):
    * Functions exceeding 50 lines of code.
    * Incorrect or missing Tailwind CSS usage.
    * Any other rule defined in the standards files.

## Output Format (MANDATORY)

Produce a Markdown report with EXACTLY this structure:

# Code Review Report — {ticket_id}

## Missing Requirements
- List each Jira acceptance criterion not addressed by the diff.
- If all requirements are met, write: "None."

## Code Quality Violations
- List each standards violation found in the diff.
- If no violations are found, write: "None."

## Suggested Fixes
- For each issue listed above, provide a concrete, actionable recommendation.
- If there are no issues, write: "None."

## Clean Pass (only when there are NO issues at all)

If and only if there are zero missing requirements AND zero code quality
violations, replace the entire report body with:

> The code satisfies all requirements and standards.

Be pedantic. Be precise. Do not omit any issue, no matter how minor.
"""

# ---------------------------------------------------------------------------
# Public factory function
# ---------------------------------------------------------------------------


def build_agent(config: AppConfig):
    """Initialise and return a ReAct agent (CompiledStateGraph) for code review.


    Constructs a ``ChatOpenAI`` client targeting the xAI Grok API, binds the
    three review tools, and wraps everything in a LangGraph ReAct agent
    configured with the Pedantic Senior Code Reviewer system prompt.

    Args:
        config: Populated ``AppConfig`` dataclass from ``load_config()``.

    Returns:
        A ready-to-invoke ``CompiledStateGraph`` instance.
    """
    # --- Initialise the Grok LLM via the OpenAI-compatible xAI endpoint ---
    llm = ChatOpenAI(
        model="grok-beta",
        base_url="https://api.x.ai/v1",
        api_key=config.xai_api_key,  # type: ignore[arg-type]
    )

    # --- Collect the three review tools in the required invocation order ---
    tools = [
        jira_context_retriever,
        git_diff_collector,
        rules_engine_reader,
    ]

    # --- Construct the ReAct agent with the system persona as the prompt ---
    # langgraph's create_react_agent accepts a plain string or SystemMessage
    # as the `prompt` parameter; it is prepended to every conversation.
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=_SYSTEM_PROMPT,
    )
