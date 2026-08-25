#!/usr/bin/env python3
"""
Git credential helper for github.com that mints a fresh GitHub App
installation token on every `get` (via github-app-token.py), so AI-driven
`git push`/`fetch`/`pull` over HTTPS authenticate as the bot automatically
-- no manual token step. Wired in only for AI harness sessions, via the
credential.https://github.com.helper git config injected through env (see
ai-tooling/claude-settings.json and the codex config.toml block) -- your
own manual git usage is untouched.

Implements the git credential helper protocol (gitcredentials(7)): `get`
reads key=value lines from stdin and prints username/password on stdout;
`store`/`erase` are no-ops since nothing is persisted -- every token is
minted fresh and expires in about an hour anyway.
"""
import os
import subprocess
import sys

TOKEN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github-app-token.py')


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''

    request = {}
    for line in sys.stdin:
        line = line.strip()
        if '=' in line:
            key, _, value = line.partition('=')
            request[key] = value

    if action != 'get' or request.get('host') != 'github.com':
        return

    result = subprocess.run([sys.executable, TOKEN_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return

    token = result.stdout.strip()
    if not token:
        return

    print('username=x-access-token')
    print(f'password={token}')


if __name__ == '__main__':
    main()
