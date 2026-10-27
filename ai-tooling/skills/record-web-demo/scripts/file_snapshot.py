from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def restore(saved: dict[Path, bytes | None]) -> list[str]:
    problems: list[str] = []
    for path, content in saved.items():
        if content is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        elif path.is_file() or path.is_symlink():
            path.unlink()
        elif path.exists():
            problems.append(f"{path} was created as a directory during the demo; left in place")
    return problems


@contextmanager
def restored_afterwards(paths: list[Path]) -> Iterator[list[str]]:
    saved = snapshot(paths)
    problems: list[str] = []
    try:
        yield problems
    finally:
        problems.extend(restore(saved))
