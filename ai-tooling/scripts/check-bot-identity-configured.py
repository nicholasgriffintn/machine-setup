#!/usr/bin/env python3
"""
Exit 0 if the GitHub App bot identity is actually usable on THIS machine,
exit 1 otherwise.

"Configured" means more than "claude-settings.json has a GITHUB_APP_ID" --
that file is git-tracked, so a fresh clone already carries whoever last
committed it's App ID and key *path*. Checking presence alone means a fresh
clone on a new machine silently skips the setup prompt (machine-setup.sh)
and installs a token refresher (sync-symlinks.sh) pointed at a private key
that was never copied there, leaving the bot identity broken with no
signal to the user. This only returns true once the private key those
settings actually point at exists locally.
"""
import json
import os
import sys
from pathlib import Path

AI_TOOLING_DIR = Path(__file__).resolve().parent.parent
CLAUDE_SETTINGS = AI_TOOLING_DIR / 'claude-settings.json'


def main():
    if not CLAUDE_SETTINGS.is_file():
        sys.exit(1)

    with open(CLAUDE_SETTINGS) as f:
        env = json.load(f).get('env', {})

    app_id = env.get('GITHUB_APP_ID', '')
    key_path = env.get('GITHUB_APP_PRIVATE_KEY_PATH', '')
    if not app_id or not key_path:
        sys.exit(1)

    if not os.path.isfile(os.path.expanduser(key_path)):
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
