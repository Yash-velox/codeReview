"""
tests/test_git_tool.py — Property-based tests for tools/git_tool.py

Tests Property 6 from the design document using Hypothesis.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

from tools.git_tool import collect_git_diff, discover_git_repository_roots, find_git_repository_root

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Any printable text including empty string — represents raw git diff output
_diff_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=0,
    max_size=512,
)

# Non-empty diff text (at least one non-whitespace character so it isn't
# treated as "no staged changes" by the implementation)
_nonempty_diff = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=512,
).filter(lambda s: s.strip() != "")


# ---------------------------------------------------------------------------
# Property 6: Git diff collector returns subprocess output as string
# ---------------------------------------------------------------------------


@given(diff_output=_nonempty_diff)
@settings(max_examples=100)
def test_git_diff_returns_exact_string(diff_output: str) -> None:
    # Feature: code-review-agent, Property 6: Git diff collector returns subprocess output as string
    # Validates: Requirements 3.1, 3.2
    #
    # For any non-empty mocked git diff output, collect_git_diff() must return
    # that exact string and must not raise an exception.

    mock_result = MagicMock()
    mock_result.stdout = diff_output
    mock_result.returncode = 0

    repo = Path("/tmp/fake-repo")
    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[repo],
        ),
        patch("tools.git_tool.subprocess.run", return_value=mock_result),
    ):
        result = collect_git_diff()

    assert isinstance(result, str), "collect_git_diff must return a string"
    assert result == diff_output, (
        f"Expected exact diff output {diff_output!r}, got {result!r}"
    )


@given(diff_output=_diff_text.filter(lambda s: s.strip() == ""))
@settings(max_examples=100)
def test_git_diff_empty_output_returns_no_staged_message(diff_output: str) -> None:
    # Feature: code-review-agent, Property 6: Git diff collector returns subprocess output as string
    # Validates: Requirements 3.2
    #
    # When git diff --staged produces empty (or whitespace-only) output,
    # collect_git_diff() must return the "No staged changes found." message.

    mock_result = MagicMock()
    mock_result.stdout = diff_output
    mock_result.returncode = 0

    repo = Path("/tmp/fake-repo")
    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[repo],
        ),
        patch("tools.git_tool.subprocess.run", return_value=mock_result),
    ):
        result = collect_git_diff()

    assert isinstance(result, str), "collect_git_diff must return a string"
    assert result == "No staged changes found.", (
        f"Expected 'No staged changes found.' for empty output, got {result!r}"
    )


@given(diff_output=_diff_text)
@settings(max_examples=100)
def test_git_diff_file_not_found_returns_error_string(diff_output: str) -> None:
    # Feature: code-review-agent, Property 6: Git diff collector returns subprocess output as string
    # Validates: Requirements 3.3
    #
    # When git is not installed (FileNotFoundError), collect_git_diff() must
    # return a non-empty error string and must not raise an exception.

    repo = Path("/tmp/fake-repo")
    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[repo],
        ),
        patch(
            "tools.git_tool.subprocess.run",
            side_effect=FileNotFoundError("git not found"),
        ),
    ):
        result = collect_git_diff()

    assert isinstance(result, str), (
        "collect_git_diff must return a string on FileNotFoundError"
    )
    assert len(result) > 0, "Returned error string must be non-empty"


@given(diff_output=_diff_text)
@settings(max_examples=100)
def test_git_diff_called_process_error_returns_error_string(diff_output: str) -> None:
    # Feature: code-review-agent, Property 6: Git diff collector returns subprocess output as string
    # Validates: Requirements 3.3
    #
    # When git exits with a non-zero code (CalledProcessError — e.g. not a git
    # repo), collect_git_diff() must return a non-empty error string and must
    # not raise an exception.

    error = subprocess.CalledProcessError(
        returncode=128,
        cmd=["git", "diff", "--staged"],
        stderr="fatal: not a git repository",
    )

    repo = Path("/tmp/fake-repo")
    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[repo],
        ),
        patch("tools.git_tool.subprocess.run", side_effect=error),
    ):
        result = collect_git_diff()

    assert isinstance(result, str), (
        "collect_git_diff must return a string on CalledProcessError"
    )
    assert len(result) > 0, "Returned error string must be non-empty"


def test_find_git_repository_root_walks_upward(tmp_path: Path) -> None:
    repo = tmp_path / "crm"
    repo.mkdir()
    (repo / ".git").mkdir()
    nested = repo / "crm_frontend" / "src"
    nested.mkdir(parents=True)
    found = find_git_repository_root(start=nested)
    assert found == repo.resolve()


def test_find_git_repository_root_returns_none_outside_git(tmp_path: Path) -> None:
    stray = tmp_path / "not-a-repo" / "a"
    stray.mkdir(parents=True)
    assert find_git_repository_root(start=stray) is None


def test_collect_git_diff_outside_git_repo_returns_clear_message() -> None:
    with patch("tools.git_tool.discover_git_repository_roots", return_value=[]):
        result = collect_git_diff()
    assert "No Git repositories found" in result


def test_collect_git_diff_passes_cwd_to_git() -> None:
    repo = Path("/tmp/fake-monorepo")
    mock_result = MagicMock(stdout="diff OK\n", returncode=0)
    mock_run = MagicMock(return_value=mock_result)

    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[repo],
        ),
        patch("tools.git_tool.subprocess.run", mock_run),
    ):
        result = collect_git_diff()

    assert result == "diff OK\n"
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs.get("cwd") == str(repo)


def test_discover_git_roots_single_monorepo_returns_only_root(tmp_path: Path) -> None:
    repo = tmp_path / "crm"
    repo.mkdir()
    (repo / ".git").mkdir()
    nested = repo / "crm_frontend" / "src"
    nested.mkdir(parents=True)
    roots = discover_git_repository_roots(start=nested)
    assert roots == [repo.resolve()]


def test_discover_git_roots_finds_sibling_repos_under_umbrella(tmp_path: Path) -> None:
    crm = tmp_path / "crm"
    crm.mkdir()
    fe = crm / "crm_frontend"
    be = crm / "crm_backend"
    fe.mkdir()
    be.mkdir()
    (fe / ".git").mkdir()
    (be / ".git").mkdir()
    roots = discover_git_repository_roots(start=crm)
    assert roots == sorted({fe.resolve(), be.resolve()})


def test_discover_git_roots_from_inside_frontend_includes_backend(tmp_path: Path) -> None:
    crm = tmp_path / "crm"
    fe = crm / "crm_frontend"
    src = fe / "src"
    be = crm / "crm_backend"
    src.mkdir(parents=True)
    be.mkdir(parents=True)
    (fe / ".git").mkdir()
    (be / ".git").mkdir()
    roots = discover_git_repository_roots(start=src)
    assert roots == sorted({fe.resolve(), be.resolve()})


def test_collect_git_diff_multi_repo_combines_sections() -> None:
    fe = Path("/tmp/fake-fe")
    be = Path("/tmp/fake-be")
    mock_fe = MagicMock(stdout="+frontend line\n", returncode=0)
    mock_be = MagicMock(stdout="+backend line\n", returncode=0)

    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[fe, be],
        ),
        patch(
            "tools.git_tool.subprocess.run",
            side_effect=[mock_fe, mock_be],
        ),
    ):
        result = collect_git_diff()

    assert str(fe) in result and str(be) in result
    assert "+frontend line" in result and "+backend line" in result


def test_collect_git_diff_multi_repo_one_empty_still_lists_both() -> None:
    fe = Path("/tmp/fake-fe")
    be = Path("/tmp/fake-be")
    mock_fe = MagicMock(stdout="+only front\n", returncode=0)
    mock_be = MagicMock(stdout="", returncode=0)

    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[fe, be],
        ),
        patch(
            "tools.git_tool.subprocess.run",
            side_effect=[mock_fe, mock_be],
        ),
    ):
        result = collect_git_diff()

    assert "+only front" in result
    assert "(no staged changes in this repository.)" in result
    assert str(be) in result


def test_collect_git_diff_multi_repo_all_empty_lists_roots() -> None:
    fe = Path("/tmp/fake-fe")
    be = Path("/tmp/fake-be")
    empty_fe = MagicMock(stdout="", returncode=0)
    empty_be = MagicMock(stdout="", returncode=0)

    with (
        patch(
            "tools.git_tool.discover_git_repository_roots",
            return_value=[fe, be],
        ),
        patch(
            "tools.git_tool.subprocess.run",
            side_effect=[empty_fe, empty_be],
        ),
    ):
        result = collect_git_diff()

    assert "No staged changes found in any of the discovered repositories" in result
    assert str(fe) in result and str(be) in result
