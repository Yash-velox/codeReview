"""
tests/test_rules_tool.py — Property-based tests for tools/rules_tool.py

Tests Properties 7–8 from the design document using Hypothesis.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from tools.rules_tool import read_coding_standards

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty printable text (no null bytes) for file content
_file_content = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=256,
)

# Valid filename stems (alphanumeric + underscores/hyphens, no extension)
_filename_stem = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-",
    ),
    min_size=1,
    max_size=32,
).filter(lambda s: s[0].isalnum())  # Must start with alphanumeric

# Strategy for a set of (filename_stem, content) pairs
# At least 1 file, up to 5 files to keep test execution reasonable
_md_files = st.lists(
    st.tuples(_filename_stem, _file_content),
    min_size=1,
    max_size=5,
    unique_by=lambda x: x[0],  # Ensure unique filenames
)


# ---------------------------------------------------------------------------
# Property 7: Standards reader consolidates all .md files under labelled headers
# ---------------------------------------------------------------------------


@given(files=_md_files)
@settings(max_examples=100)
def test_standards_consolidation(files: list[tuple[str, str]]) -> None:
    # Feature: code-review-agent, Property 7: Standards reader consolidates all .md files under labelled headers
    # Validates: Requirements 4.1, 4.2
    #
    # For any directory containing one or more .md files with arbitrary content,
    # read_coding_standards() must return a single string that contains each
    # filename as a section header and each file's full content, with no file
    # omitted.

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create all the .md files in the temp directory
        for stem, content in files:
            md_file = temp_path / f"{stem}.md"
            md_file.write_text(content, encoding="utf-8")

        # Patch the module-level _STANDARDS_DIR to point to our temp directory
        with patch("tools.rules_tool._STANDARDS_DIR", temp_path):
            result = read_coding_standards()

    assert isinstance(result, str), "read_coding_standards must return a string"

    # Verify each file's header and content appear in the result
    for stem, content in files:
        expected_header = f"## Standards: {stem}"
        assert expected_header in result, (
            f"Expected header {expected_header!r} not found in result"
        )
        assert content in result, (
            f"Expected content from {stem}.md not found in result"
        )

    # Verify no file was omitted: count the number of section headers
    header_count = result.count("## Standards:")
    assert header_count == len(files), (
        f"Expected {len(files)} section headers, found {header_count}"
    )


# ---------------------------------------------------------------------------
# Property 8: Missing or empty standards directory returns error string, no exception
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(st.integers())
def test_standards_missing_dir_returns_string(seed: int) -> None:
    # Feature: code-review-agent, Property 8: Missing or empty standards directory returns error string, no exception
    # Validates: Requirements 4.3
    #
    # When the standards directory does not exist, read_coding_standards()
    # must return a non-empty descriptive string and must not raise an exception.

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        # Point to a subdirectory that does NOT exist
        missing_dir = temp_path / "nonexistent_standards"

        with patch("tools.rules_tool._STANDARDS_DIR", missing_dir):
            result = read_coding_standards()

    assert isinstance(result, str), (
        "read_coding_standards must return a string when directory is missing"
    )
    assert len(result) > 0, "Returned error string must be non-empty"
    assert "error" in result.lower() or "does not exist" in result.lower(), (
        "Error string should indicate the directory does not exist"
    )


@settings(max_examples=100)
@given(st.integers())
def test_standards_empty_dir_returns_string(seed: int) -> None:
    # Feature: code-review-agent, Property 8: Missing or empty standards directory returns error string, no exception
    # Validates: Requirements 4.3
    #
    # When the standards directory exists but contains no .md files,
    # read_coding_standards() must return a non-empty descriptive string
    # and must not raise an exception.

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        # Create an empty directory (or one with non-.md files)
        empty_standards = temp_path / "empty_standards"
        empty_standards.mkdir()

        # Optionally add a non-.md file to ensure it's ignored
        (empty_standards / "readme.txt").write_text("Not a markdown file")

        with patch("tools.rules_tool._STANDARDS_DIR", empty_standards):
            result = read_coding_standards()

    assert isinstance(result, str), (
        "read_coding_standards must return a string when directory is empty"
    )
    assert len(result) > 0, "Returned error string must be non-empty"
    assert "error" in result.lower() or "no markdown" in result.lower(), (
        "Error string should indicate no .md files were found"
    )
