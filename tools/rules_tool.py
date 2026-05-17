"""
tools/rules_tool.py — RulesEngineReader

Reads all Markdown files from the local ``standards/`` directory and
concatenates their contents into a single consolidated context string.
Each file is placed under a labelled section header derived from its stem.

Exposes the function as a LangChain Tool for use by the ReAct agent.
"""

from pathlib import Path

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Locate the standards directory relative to the workspace root.
# We resolve from this file's location (tools/) up one level to the project
# root, then descend into standards/.  This keeps the path portable across
# different working directories.
# ---------------------------------------------------------------------------
_STANDARDS_DIR = Path(__file__).resolve().parent.parent / "standards"


def read_coding_standards(_: str = "") -> str:
    """Scan the ``standards/`` directory and return all ``.md`` files as one string.

    The optional ignored argument (``_``) exists solely to satisfy the
    LangChain Tool interface, which always passes a string input to the
    wrapped function.

    Each file's content is placed under a section header of the form::

        ## Standards: {filename_stem}

    Sections are separated by a double newline.

    Returns:
        A consolidated string containing every ``.md`` file's content when
        at least one file is found.
        A descriptive error string (no exception raised) when the directory
        does not exist or contains no ``.md`` files.
    """
    # --- Verify the standards directory exists ---
    if not _STANDARDS_DIR.exists() or not _STANDARDS_DIR.is_dir():
        return (
            f"Error: Standards directory '{_STANDARDS_DIR}' does not exist. "
            "Create a 'standards/' directory at the project root and add "
            "Markdown rule files to it."
        )

    # --- Collect all .md files, sorted for deterministic output ---
    md_files = sorted(_STANDARDS_DIR.glob("*.md"))

    if not md_files:
        return (
            f"Error: No Markdown (.md) files found in '{_STANDARDS_DIR}'. "
            "Add at least one .md rule file to the standards/ directory."
        )

    # --- Build one section per file and join them ---
    sections = []
    for md_file in md_files:
        # Use the file stem (e.g. "clean_code") as the section label
        header = f"## Standards: {md_file.stem}"
        content = md_file.read_text(encoding="utf-8")
        sections.append(f"{header}\n{content}")

    # Separate sections with a double newline for readability
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# LangChain Tool registration (structured schema — required for Groq tool calling)
# ---------------------------------------------------------------------------


@tool
def rules_engine_reader() -> str:
    """Load all Markdown files from ``standards/`` into one labelled string."""
    return read_coding_standards("")
