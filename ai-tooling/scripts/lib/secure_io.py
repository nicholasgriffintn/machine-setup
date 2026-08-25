#!/usr/bin/env python3
"""
Shared write helpers for the files that carry the bot identity's live
credentials (claude-settings.local.json, ~/.claude/settings.json,
~/.codex/config.toml): write-then-rename so a reader never sees a
half-written file, and lock permissions to the owner so a live GH_TOKEN
isn't left world-readable by the process umask.
"""
import os
from pathlib import Path

SECRET_FILE_MODE = 0o600


def write_text_atomic(path, text: str, mode: int = SECRET_FILE_MODE) -> None:
    path = Path(path)
    tmp_path = path.with_name(f'.{path.name}.tmp')
    tmp_path.write_text(text)
    os.chmod(tmp_path, mode)
    os.replace(tmp_path, path)


def write_json_atomic(path: Path, data, mode: int = SECRET_FILE_MODE) -> None:
    import json
    write_text_atomic(path, json.dumps(data, indent=2) + '\n', mode)
