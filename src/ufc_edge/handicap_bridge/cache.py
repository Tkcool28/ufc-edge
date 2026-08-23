from __future__ import annotations

from pathlib import Path
import shutil


def _inside(root: Path, path: Path) -> bool:
    root_r = root.resolve()
    path_r = path.resolve()
    return path_r == root_r or root_r in path_r.parents


def request_dir(cache_root: Path, issue_number: int) -> Path:
    if issue_number <= 0:
        raise ValueError("issue_number must be positive")
    root = cache_root.resolve()
    path = root / "handicap" / "requests" / str(issue_number)
    if not _inside(root, path):
        raise ValueError("unsafe cache path")
    return path


def replace_request_dir(cache_root: Path, issue_number: int, staged_request_dir: Path) -> Path:
    target = request_dir(cache_root, issue_number)
    source = staged_request_dir.resolve()
    if not source.is_dir():
        raise ValueError("staged request directory does not exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target


def prune_cache(cache_root: Path, keep: int = 20) -> list[str]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    root = cache_root.resolve()
    requests = root / "handicap" / "requests"
    if not requests.exists():
        return []
    candidates = [p for p in requests.iterdir() if p.is_dir() and p.name.isdigit()]
    candidates.sort(key=lambda p: int(p.name), reverse=True)
    removed: list[str] = []
    for path in candidates[keep:]:
        if not _inside(requests, path):
            raise ValueError("refusing to prune outside cache request root")
        shutil.rmtree(path)
        removed.append(path.name)
    return removed
