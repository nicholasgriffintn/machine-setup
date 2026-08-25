#!/usr/bin/env python3
"""
git pre-commit hook: scans staged file contents against the same secret
patterns security-check.py uses on Edit/Write, and blocks the commit on a
match. That hook only ever sees content going through the AI harness's own
Edit/Write tools; this is the backstop for every other way a secret can end
up staged -- a manual `git add`, a script writing straight to a tracked
file (see ai-tooling/scripts/set-ai-env.py's --local requirement), or a
hook bug. Installed via `git config core.hooksPath .githooks` (see
.githooks/pre-commit), which sync-symlinks.sh sets up.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from config import get_secret_patterns  # noqa: E402


def staged_files():
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True, check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def staged_content(path: str):
    result = subprocess.run(
        ['git', 'show', f':{path}'], capture_output=True, check=True,
    )
    return result.stdout


def main():
    patterns, skip_files = get_secret_patterns()
    found = []

    for path in staged_files():
        if Path(path).name in skip_files:
            continue
        try:
            raw = staged_content(path)
        except subprocess.CalledProcessError:
            continue
        if b'\0' in raw:
            continue  # binary file
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        for pattern, label in patterns:
            if re.search(pattern, text):
                found.append((path, label))

    if found:
        print("BLOCKED: secret-shaped content in staged changes:", file=sys.stderr)
        for path, label in found:
            print(f"  {path}: matches {label}", file=sys.stderr)
        print(
            "\nIf this is a live credential, keep it out of tracked files "
            "(see ai-tooling/scripts/set-ai-env.py --local). "
            "If it's a false positive, commit with --no-verify.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
