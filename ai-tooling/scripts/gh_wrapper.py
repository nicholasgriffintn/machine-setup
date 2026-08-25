#!/usr/bin/env python3
"""Run GitHub CLI with the current short-lived GitHub App token.

AI harness processes can live longer than a GitHub App installation token.
Reading GH_TOKEN only when the harness starts therefore leaves long-running
Claude and Codex sessions with an expired credential. This wrapper reloads
the token maintained by refresh-gh-token.py for every gh invocation.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_SETTINGS = SCRIPT_DIR.parent / 'claude-settings.local.json'
REFRESH_SCRIPT = SCRIPT_DIR / 'refresh-gh-token.py'
MAX_TOKEN_AGE_SECONDS = 45 * 60


def load_token(settings_path: Path) -> Optional[str]:
    try:
        with settings_path.open() as settings_file:
            token = json.load(settings_file).get('env', {}).get('GH_TOKEN')
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return token.strip() if isinstance(token, str) and token.strip() else None


def token_is_stale(settings_path: Path, now: Optional[float] = None) -> bool:
    try:
        modified_at = settings_path.stat().st_mtime
    except OSError:
        return True
    return (time.time() if now is None else now) - modified_at >= MAX_TOKEN_AGE_SECONDS


def refresh_token() -> None:
    subprocess.run(
        [sys.executable, str(REFRESH_SCRIPT), '--if-stale'],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def find_real_gh(path_value: str, wrapper_path: Path) -> Path:
    wrapper_target = wrapper_path.resolve()
    for directory in path_value.split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / 'gh'
        try:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                if candidate.resolve() != wrapper_target:
                    return candidate
        except OSError:
            continue
    raise FileNotFoundError('Could not find the real gh executable after the credential wrapper')


def bot_environment(base_environment: Dict[str, str], token: str) -> Dict[str, str]:
    child_environment = base_environment.copy()
    child_environment['GH_TOKEN'] = token
    child_environment.pop('GITHUB_TOKEN', None)
    return child_environment


def main() -> None:
    real_gh = find_real_gh(os.environ.get('PATH', ''), Path(__file__))
    arguments = [str(real_gh), *sys.argv[1:]]

    # The shim is globally discoverable, but manual shells must retain the
    # user's normal gh identity. This marker is injected only by the managed
    # Claude/Codex environment policy.
    if not os.environ.get('AI_GIT_ALLOWED_OWNERS'):
        os.execvpe(str(real_gh), arguments, os.environ.copy())

    if token_is_stale(LOCAL_SETTINGS) or load_token(LOCAL_SETTINGS) is None:
        refresh_token()

    token = load_token(LOCAL_SETTINGS)
    if token is None:
        raise RuntimeError(f'No GH_TOKEN found in {LOCAL_SETTINGS} after refresh')

    os.execvpe(str(real_gh), arguments, bot_environment(os.environ, token))


if __name__ == '__main__':
    main()
