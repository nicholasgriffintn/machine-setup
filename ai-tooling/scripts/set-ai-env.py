#!/usr/bin/env python3
"""
Merges KEY=VALUE pairs into claude-settings.json's "env" block (or its
untracked local overlay), the mechanism Claude Code actually applies to
every Bash tool call regardless of shell type -- unlike ~/.zshrc(.local),
which only loads for interactive shells and is never sourced by the
non-interactive shells AI harnesses use.

Use --local for anything that's a live credential (e.g. GH_TOKEN): the
base file is git-tracked, so a secret written there ships to GitHub on
the next commit. The local overlay is gitignored and only ever touches
the live ~/.claude/settings.json via render-claude-settings.py.

Usage: set-ai-env.py [--local] KEY1=VALUE1 [KEY2=VALUE2 ...]
"""
import json
import subprocess
import sys
from pathlib import Path

AI_TOOLING_DIR = Path(__file__).resolve().parent.parent
BASE_SETTINGS = AI_TOOLING_DIR / 'claude-settings.json'
LOCAL_SETTINGS = AI_TOOLING_DIR / 'claude-settings.local.json'
RENDER_SCRIPT = Path(__file__).resolve().parent / 'render-claude-settings.py'


def main():
    args = sys.argv[1:]
    local = '--local' in args
    if local:
        args.remove('--local')

    if not args:
        print("Usage: set-ai-env.py [--local] KEY1=VALUE1 [KEY2=VALUE2 ...]", file=sys.stderr)
        sys.exit(1)

    target = LOCAL_SETTINGS if local else BASE_SETTINGS

    settings = {}
    if target.is_file():
        with open(target) as f:
            settings = json.load(f)

    settings.setdefault('env', {})
    for pair in args:
        key, _, value = pair.partition('=')
        settings['env'][key] = value

    with open(target, 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')

    print(f"Updated {target}")
    subprocess.run(['python3', str(RENDER_SCRIPT)], check=True)


if __name__ == '__main__':
    main()
