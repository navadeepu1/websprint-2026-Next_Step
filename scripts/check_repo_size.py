"""Fail if the tracked working tree is too large for challenge submission."""

from __future__ import annotations

import sys
from pathlib import Path

MAX_REPO_BYTES = 10 * 1024 * 1024
MAX_FILE_BYTES = 500 * 1024
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
}


def _should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in SKIP_DIR_NAMES for part in rel_parts)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    total = 0
    oversized: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _should_skip(path, root):
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_FILE_BYTES:
            oversized.append(f"{path.relative_to(root)} ({size} bytes)")
    errors: list[str] = []
    if oversized:
        errors.append("Files over 500 KB:\n  " + "\n  ".join(oversized))
    if total > MAX_REPO_BYTES:
        errors.append(f"Repository size {total} bytes exceeds 10 MB.")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Repository size OK: {total} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
