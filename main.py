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


def _parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments.

    Defines a single positional argument, ``ticket_id``, which is the Jira
    issue key the agent will review against (e.g. ``PROJ-123``).
    """
    # Set up the argument parser with a helpful description
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Run the Code Review Agent against a Jira ticket.",
    )

    # Positional argument: the Jira ticket ID to review
    parser.add_argument(
        "ticket_id",
        help="Jira ticket ID to review against (e.g. PROJ-123)",
    )

    return parser.parse_args()


def main() -> None:
    """Entry point: parse args, build agent, run review, print report.

    Orchestrates the full review pipeline:
    1. Parse the ticket_id from CLI arguments.
    2. Load environment configuration via load_config().
    3. Build the ReAct agent via build_agent(config).
    4. Invoke the agent with the ticket_id as the user message.
    5. Extract and print the final Markdown report to stdout.

    On EnvironmentError (missing env vars), prints a human-readable message
    to stderr and exits with code 1.

    On RuntimeError (LLM or agent failure), prints a human-readable message
    to stderr and exits with code 2.
    """
    # --- Step 1: Parse the ticket_id from CLI arguments ---
    args = _parse_args()
    ticket_id: str = args.ticket_id

    try:
        # --- Step 2: Load and validate environment configuration ---
        # Raises EnvironmentError if any required variable is missing
        config = load_config()

        # --- Step 3: Build the ReAct agent with the loaded config ---
        agent = build_agent(config)

        # --- Step 4: Run the agent with the ticket_id as the user message ---
        # The agent expects a dict with a "messages" key containing a list of
        # (role, content) tuples; the ticket_id is the human's input prompt.
        result = agent.invoke({"messages": [("human", ticket_id)]})

        # --- Step 5: Extract the final report from the last message ---
        # The agent appends its final response as the last message in the list
        report: str = result["messages"][-1].content

        # Print the Markdown report to stdout
        print(report)

    except EnvironmentError as exc:
        # Configuration error — missing or invalid environment variables
        print(
            f"Configuration error: {exc}\n"
            "Please check your .env file and ensure all required variables are set.",
            file=sys.stderr,
        )
        sys.exit(1)

    except RuntimeError as exc:
        # Runtime error — typically an LLM API failure propagated from agent.py
        print(
            f"Agent runtime error: {exc}\n"
            "The review could not be completed. Check your API key and network connectivity.",
            file=sys.stderr,
        )
        sys.exit(2)


# Standard Python entry-point guard — only run main() when executed directly
if __name__ == "__main__":
    main()
