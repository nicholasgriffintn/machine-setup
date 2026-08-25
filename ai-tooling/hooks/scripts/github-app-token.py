#!/usr/bin/env python3
"""
Mints a short-lived GitHub App installation access token for the bot
identity, so AI-driven git pushes / API calls can authenticate as the app
itself instead of the user's personal credentials.

Reads GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY_PATH from the environment
(never from arguments or files in this repo) and prints the installation
token to stdout on success. Nothing here ever sees or stores the private
key's contents beyond handing its path to openssl.

Usage:
    GH_TOKEN=$(python3 github-app-token.py) \\
        git push https://x-access-token:$GH_TOKEN@github.com/OWNER/REPO.git HEAD
"""
import base64
import json
import os
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

APP_ID_VAR = 'GITHUB_APP_ID'
PRIVATE_KEY_PATH_VAR = 'GITHUB_APP_PRIVATE_KEY_PATH'


def target_owner() -> str:
    return os.environ.get('AI_GIT_ALLOWED_OWNERS', 'nicholasgriffintn').split(',')[0].strip()


def fail_with_setup_instructions(reason: str):
    key_path_example = '~/.config/github-app/nicholas-clanker.pem'
    print(f"🚫 {reason}", file=sys.stderr)
    print(file=sys.stderr)
    print("Set these in your shell profile and open a new shell:", file=sys.stderr)
    print(f"  export {APP_ID_VAR}=<App ID, from the app's settings page>", file=sys.stderr)
    print(f"  export {PRIVATE_KEY_PATH_VAR}={key_path_example}", file=sys.stderr)
    print(file=sys.stderr)
    print("Get the .pem from the app's settings page (\"Generate a private key\"),", file=sys.stderr)
    print(f"save it to that path, then: chmod 600 {key_path_example}", file=sys.stderr)
    sys.exit(1)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def build_jwt(app_id: str, key_path: str) -> str:
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
    signing_input = f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(payload).encode())}"

    result = subprocess.run(
        ['openssl', 'dgst', '-sha256', '-sign', key_path],
        input=signing_input.encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        fail_with_setup_instructions(
            f"openssl failed to sign the JWT with {key_path}: {result.stderr.decode().strip()}"
        )
    return f"{signing_input}.{b64url(result.stdout)}"


def api_request(url: str, jwt: str, method: str = 'GET'):
    req = urllib.request.Request(url, method=method, headers={
        'Authorization': f'Bearer {jwt}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"🚫 GitHub API error ({exc.code}) calling {url}: {exc.read().decode()}", file=sys.stderr)
        sys.exit(1)


def main():
    app_id = os.environ.get(APP_ID_VAR)
    key_path = os.environ.get(PRIVATE_KEY_PATH_VAR)

    if not app_id or not key_path:
        fail_with_setup_instructions(f"{APP_ID_VAR} and {PRIVATE_KEY_PATH_VAR} must both be set")

    key_path = os.path.expanduser(key_path)
    if not os.path.isfile(key_path):
        fail_with_setup_instructions(f"Private key not found at {key_path}")

    key_mode = stat.S_IMODE(os.stat(key_path).st_mode)
    if key_mode & (stat.S_IRWXG | stat.S_IRWXO):
        fail_with_setup_instructions(
            f"{key_path} is readable by group/other (mode {oct(key_mode)}). "
            f"This key can mint tokens for every installation of the app -- "
            f"run: chmod 600 {key_path}"
        )

    jwt = build_jwt(app_id, key_path)

    owner = target_owner()
    installations = api_request('https://api.github.com/app/installations', jwt)
    match = next(
        (i for i in installations if i.get('account', {}).get('login', '').lower() == owner.lower()),
        None,
    )
    if not match:
        print(f"🚫 No installation of this app found for account '{owner}'. "
              f"Install it from the app's settings page first.", file=sys.stderr)
        sys.exit(1)

    token_resp = api_request(
        f"https://api.github.com/app/installations/{match['id']}/access_tokens", jwt, method='POST'
    )
    print(token_resp['token'])


if __name__ == '__main__':
    main()
