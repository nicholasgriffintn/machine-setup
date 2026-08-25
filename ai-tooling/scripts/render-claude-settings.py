#!/usr/bin/env python3
"""
Generates ~/.claude/settings.json from the tracked base config plus an
untracked local overlay (claude-settings.local.json, gitignored).

settings.json used to be symlinked straight into the repo, which meant any
live secret written into its "env" block (e.g. a refreshed GH_TOKEN) landed
directly in a git-tracked file. The overlay keeps secrets out of git while
still reaching the live file every AI harness actually reads.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.secure_io import write_json_atomic  # noqa: E402

AI_TOOLING_DIR = Path(__file__).resolve().parent.parent
BASE = AI_TOOLING_DIR / 'claude-settings.json'
LOCAL = AI_TOOLING_DIR / 'claude-settings.local.json'
TARGET = Path.home() / '.claude' / 'settings.json'


def main():
    with open(BASE) as f:
        settings = json.load(f)

    if LOCAL.is_file():
        with open(LOCAL) as f:
            local = json.load(f)
        settings.setdefault('env', {}).update(local.get('env', {}))

    if TARGET.is_symlink():
        TARGET.unlink()

    write_json_atomic(TARGET, settings)

    print(f"Rendered {TARGET}")


if __name__ == '__main__':
    main()
