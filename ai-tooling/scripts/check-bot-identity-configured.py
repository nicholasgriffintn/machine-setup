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
settings actually point at exists locally AND has permissions
github-app-token.py will actually accept -- it fails closed on a
group/other-readable key, so a 0644 file would otherwise pass this check
and then fail every single refresh with no prompt to fix it.
"""
import json
import os
import stat
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

    key_path = os.path.expanduser(key_path)
    if not os.path.isfile(key_path):
        sys.exit(1)

    # Matches github-app-token.py's own permission gate exactly.
    key_mode = stat.S_IMODE(os.stat(key_path).st_mode)
    if key_mode & (stat.S_IRWXG | stat.S_IRWXO):
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
