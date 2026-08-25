#!/usr/bin/env python3
"""
Mints a fresh GitHub App installation token and writes it into
claude-settings.json's "env" block as GH_TOKEN, syncing to Codex too.

The ~/.local/bin/gh wrapper reads the refreshed GH_TOKEN from the local
overlay for every invocation, bypassing its own stored auth entirely. This
keeps long-running Claude and Codex sessions from retaining an expired token.
Installation tokens expire in ~1hr, so this is meant to run on a schedule
(see the launchd agent installed by sync-symlinks.sh), not just once.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AI_TOOLING_DIR = SCRIPT_DIR.parent
CLAUDE_SETTINGS = AI_TOOLING_DIR / 'claude-settings.json'
TOKEN_SCRIPT = AI_TOOLING_DIR / 'hooks' / 'scripts' / 'github-app-token.py'
SET_ENV_SCRIPT = SCRIPT_DIR / 'set-ai-env.py'
SYNC_CODEX_SCRIPT = SCRIPT_DIR / 'sync-codex-env.py'


def main():
    with open(CLAUDE_SETTINGS) as f:
        env = json.load(f).get('env', {})

    app_id = env.get('GITHUB_APP_ID')
    key_path = env.get('GITHUB_APP_PRIVATE_KEY_PATH')
    if not app_id or not key_path:
        print("GITHUB_APP_ID/GITHUB_APP_PRIVATE_KEY_PATH not set in claude-settings.json yet", file=sys.stderr)
        sys.exit(1)

    child_env = {**os.environ, 'GITHUB_APP_ID': app_id, 'GITHUB_APP_PRIVATE_KEY_PATH': key_path}
    result = subprocess.run(['python3', str(TOKEN_SCRIPT)], capture_output=True, text=True, env=child_env)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    token = result.stdout.strip()

    # --local: GH_TOKEN is a live credential and must never land in the
    # git-tracked base settings file.
    subprocess.run(['python3', str(SET_ENV_SCRIPT), '--local', f'GH_TOKEN={token}'], check=True)

    codex_config = Path.home() / '.codex' / 'config.toml'
    if codex_config.is_file():
        subprocess.run(['python3', str(SYNC_CODEX_SCRIPT)], check=True)

    print("GH_TOKEN refreshed")


if __name__ == '__main__':
    main()
