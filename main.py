"""
main.py — CLI Entry Point

Parses a Jira ticket ID from the command line, builds the code-review agent,
runs the review, and prints the resulting Markdown report to stdout.

Usage:
    python main.py TICKET_ID

Example:
    python main.py PROJ-123

Exit codes:
    0 — review completed successfully
    1 — environment configuration error (missing or invalid env vars)
    2 — runtime error (e.g. LLM API failure)
"""

import argparse
import sys

from agent import build_agent
from config import load_config

_REPORT_HEADING_MARKER = "# Code Review Report —"


def _normalize_cli_report(text: str) -> str:
    """Trim chain-of-thought if the model wrote text before the mandated H1."""
    if not text:
        return text
    idx = text.find(_REPORT_HEADING_MARKER)
    if idx <= 0:
        return text
    return text[idx:].strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Run the Code Review Agent against a Jira ticket.",
    )
    parser.add_argument(
        "ticket_id",
        help="Jira ticket ID to review against (e.g. PROJ-123)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    ticket_id: str = args.ticket_id

    try:
        config = load_config()
        agent = build_agent(config)
        result = agent.invoke({"messages": [("human", ticket_id)]})
        report: str = _normalize_cli_report(str(result["messages"][-1].content))
        print(report)

    except EnvironmentError as exc:
        print(
            f"Configuration error: {exc}\n"
            "Please check ~/code_Agent/.env (GROQ_API_KEY plus JIRA_* variables).",
            file=sys.stderr,
        )
        sys.exit(1)

    except RuntimeError as exc:
        print(
            f"Agent runtime error: {exc}\n"
            "The review could not be completed. Check your API key and network connectivity.",
            file=sys.stderr,
        )
        sys.exit(2)

    except Exception as exc:
        _mod = getattr(type(exc), "__module__", "")
        if (
            _mod.startswith("openai")
            or _mod.startswith("httpx")
            or "APIError" in type(exc).__name__
            or "BadRequest" in type(exc).__name__
            or "PermissionDenied" in type(exc).__name__
        ):
            detail = str(exc)
            low = detail.lower()
            status = getattr(exc, "status_code", None)

            # xAI-style billing denial (unlikely if using Groq, but harmless to detect)
            xai_billing = (
                ("x.ai" in low or "console.x.ai" in low)
                and status == 403
                and ("credit" in low or "licen" in low)
            )

            if xai_billing:
                print(
                    f"xAI billing / access ({type(exc).__name__}): {detail}\n",
                    file=sys.stderr,
                )
                print(
                    "Add credits/licenses for that provider in their console if you switched back to xAI.\n",
                    file=sys.stderr,
                )
            elif status == 429 or "rate limit" in low or "429" in low:
                print(
                    f"Rate limit ({type(exc).__name__}): {detail}\n\n"
                    "Groq applies per-minute/request limits — wait briefly and retry, "
                    "or upgrade your Groq tier.\n",
                    file=sys.stderr,
                )
            else:
                print(
                    f"LLM API error ({type(exc).__name__}): {detail}\n\n"
                    "Check GROQ_API_KEY and GROQ_MODEL in ~/code_Agent/.env.\n"
                    "Create keys at https://console.groq.com/keys\n"
                    "Model list: https://console.groq.com/docs/models",
                    file=sys.stderr,
                )
            sys.exit(2)
        raise


if __name__ == "__main__":
    main()
