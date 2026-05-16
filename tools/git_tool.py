"""
tools/git_tool.py — GitDiffCollector

Captures staged code changes by running ``git diff --staged`` via subprocess and
exposes the logic as a LangChain Tool.

Discovers one or more Git repository roots near the current working directory:

- Every ancestor of cwd that contains ``.git`` (classic walk-up).
- Immediate child folders named ``*/.git`` under those ancestors, but only for
  the first ``_MAX_PARENT_DIRS_FOR_SIBLING_SCAN`` hops upward from cwd — so an
  umbrella folder such as ``crm/`` with separate ``crm_frontend`` and
  ``crm_backend`` clones yields both repos and one combined diff payload.

No credentials are required.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from langchain_core.tools import Tool

# Parent hops starting at cwd that may trigger sibling-repo discovery (scanning
# immediate children for nested ``.git``). Limits accidental scans far up the tree.
_MAX_PARENT_DIRS_FOR_SIBLING_SCAN = 24

# ---------------------------------------------------------------------------
# Repository discovery
# ---------------------------------------------------------------------------


def find_git_repository_root(start: Path | None = None) -> Path | None:
    """Walk upward from ``start`` (default: cwd) for the nearest ``.git``.

    Returns:
        Absolute path to that directory, or ``None`` if none is found.

    Note:
        For reviews spanning sibling repos (separate clones under one folder),
        prefer ``discover_git_repository_roots()`` which aggregates multiple roots.
    """
    current = (start if start is not None else Path.cwd()).resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _git_child_repository_dirs(parent: Path) -> list[Path]:
    """Return resolved paths of immediate child directories that look like repo roots."""
    found: list[Path] = []
    try:
        for child in parent.iterdir():
            try:
                if child.is_dir() and (child / ".git").exists():
                    found.append(child.resolve())
            except OSError:
                continue
    except OSError:
        pass
    return found


def discover_git_repository_roots(start: Path | None = None) -> list[Path]:
    """Collect Git repo roots relevant to cwd (multi-repo aware).

    Builds the ancestor chain from ``start`` (default cwd) up to the filesystem
    root. Includes:

    - Any directory on that chain that contains ``.git``.
    - Any immediate subdirectory ``child/.git`` of a chain directory that does
      *not* itself contain ``.git``, but only for chain indices below
      ``_MAX_PARENT_DIRS_FOR_SIBLING_SCAN``.

    Returns:
        Sorted list of unique absolute repo root paths.
    """
    roots: set[Path] = set()
    cwd = (start if start is not None else Path.cwd()).resolve()

    chain: list[Path] = []
    cur = cwd
    while True:
        chain.append(cur)
        parent = cur.parent
        if parent == cur:
            break
        cur = parent

    for d in chain:
        if (d / ".git").exists():
            roots.add(d.resolve())

    for i, d in enumerate(chain):
        if i >= _MAX_PARENT_DIRS_FOR_SIBLING_SCAN:
            break
        if not (d / ".git").exists():
            for child_repo in _git_child_repository_dirs(d):
                roots.add(child_repo)

    return sorted(roots)


def _run_git_diff_staged(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(repo_root),
    )


# ---------------------------------------------------------------------------
# Core diff collection function
# ---------------------------------------------------------------------------


def collect_git_diff(_: str = "") -> str:
    """Run ``git diff --staged`` for each discovered repo root and concatenate.

    The optional ignored argument (``_``) exists solely to satisfy the LangChain
    Tool interface.

    Returns:
        **Single repo:** Raw ``git diff --staged`` stdout, or ``No staged changes found.``
        **Multiple repos:** Labeled sections per root (including repos with nothing staged).
        Errors when discovery/git fails — never raises.
    """
    try:
        repo_roots = discover_git_repository_roots()
        if not repo_roots:
            return (
                "Error: No Git repositories found near the current directory "
                "(no ``.git`` on the cwd→root path and no sibling repos discovered)."
            )

        # --- Classic single-repository behaviour (unchanged output shape) ---
        if len(repo_roots) == 1:
            repo_root = repo_roots[0]
            try:
                result = _run_git_diff_staged(repo_root)
            except subprocess.CalledProcessError as exc:
                stderr_detail = (
                    exc.stderr.strip() if exc.stderr else "no details available"
                )
                return (
                    f"Error: 'git diff --staged' failed (exit code {exc.returncode}). "
                    f"Details: {stderr_detail}"
                )
            if not result.stdout.strip():
                return "No staged changes found."
            return result.stdout

        sections: list[str] = []
        any_staged = False

        for repo_root in repo_roots:
            label = f"===== Repository: {repo_root} ====="
            try:
                result = _run_git_diff_staged(repo_root)
            except subprocess.CalledProcessError as exc:
                stderr_detail = (
                    exc.stderr.strip() if exc.stderr else "no details available"
                )
                return (
                    f"Error: 'git diff --staged' failed for {repo_root} "
                    f"(exit code {exc.returncode}). Details: {stderr_detail}"
                )

            body = result.stdout.strip()
            if body:
                any_staged = True
                sections.append(f"{label}\n{result.stdout}")
            else:
                sections.append(
                    f"{label}\n(no staged changes in this repository.)"
                )

        if not any_staged:
            listing = "\n".join(f"- {r}" for r in repo_roots)
            return (
                "No staged changes found in any of the discovered repositories:\n"
                f"{listing}"
            )

        return "\n\n".join(sections)

    except FileNotFoundError:
        return (
            "Error: 'git' command not found. "
            "Ensure git is installed and available on your PATH."
        )
    except Exception as exc:  # noqa: BLE001
        return f"Error: Unexpected error while running git diff: {exc}"


# ---------------------------------------------------------------------------
# LangChain Tool registration
# ---------------------------------------------------------------------------

git_diff_collector = Tool(
    name="git_diff_collector",
    func=collect_git_diff,
    description=(
        "Captures staged changes via `git diff --staged`. Discovers **all** Git "
        "repos tied to cwd: repos on the path from cwd upward, plus sibling "
        "folders under the same umbrella that each have their own `.git` "
        "(typical frontend/backend split). Concatenates labeled diffs when "
        "multiple repos apply so one review can cover both. "
        "Takes no meaningful input. "
        "Returns combined diff text, a no-staged message listing repos checked, "
        "or an error string."
    ),
)
