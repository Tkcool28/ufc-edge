from __future__ import annotations

from pathlib import Path


def resolve_output_root(repo_root: Path | str, requested: Path | str | None = None) -> Path:
    """Resolve an H00 output root without permitting repo-local DATA contamination.

    Normal repository-local output must live beneath ``<repo>/handicap``. An
    explicitly supplied path outside the repository is allowed so isolated tests
    and temporary validation runs can write to disposable directories.
    """

    repo = Path(repo_root).resolve()
    handicap = (repo / "handicap").resolve()
    resolved = (Path(requested) if requested is not None else handicap).resolve()

    try:
        resolved.relative_to(repo)
        inside_repo = True
    except ValueError:
        inside_repo = False

    if inside_repo and resolved != handicap and handicap not in resolved.parents:
        raise ValueError(
            "H00 repo-local output must remain beneath "
            f"{handicap}; refused destination {resolved}"
        )
    return resolved
