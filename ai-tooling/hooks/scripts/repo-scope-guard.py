#!/usr/bin/env python3
"""
PreToolUse hook (Bash matcher) that scopes both the `git` and `gh` CLIs to
an allow-list of GitHub owners/orgs (see lib/config.py: get_allowed_git_owners).

Fails CLOSED on an unexpected internal error (blocks rather than silently
allowing the command through), unlike BaseHook's default fail-open handling,
since a guard that fails open on its own bugs isn't a guard.
"""
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from config import get_allowed_git_owners  # noqa: E402

SEGMENT_SPLIT_RE = re.compile(r'&&|\|\||[;|\n]')
GITHUB_HOST_RE = re.compile(
    r'^(?:https?://|ssh://)?(?:[^@/]+@)?github\.com[:/]+([^/]+)/', re.IGNORECASE
)
OWNER_REPO_RE = re.compile(r'^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$')
API_REPOS_PATH_RE = re.compile(r'(?:^|/)repos/([^/]+)/[^/]+')

GIT_SAFE_SUBCOMMANDS = {
    '--version', '-v', '--help', 'help', 'init', 'config', 'version',
}
GIT_URL_ARG_SUBCOMMANDS = {'clone', 'ls-remote'}
GIT_REMOTE_URL_SUBCOMMANDS = {'push', 'pull', 'fetch'}

GH_SAFE_SUBCOMMANDS = {
    'auth', 'config', 'alias', 'extension', 'completion', 'help',
    'version', '--version', '-v', 'status', 'search', 'gist',
}
GH_REPO_TARGET_ACTIONS = {
    'clone', 'view', 'fork', 'delete', 'rename', 'archive', 'unarchive', 'edit', 'sync',
}


def owner_from_github_url(url: str):
    match = GITHUB_HOST_RE.match(url.strip())
    if not match:
        return None
    return match.group(1).lower()


def owner_from_owner_repo(value: str):
    if OWNER_REPO_RE.match(value):
        return value.split('/', 1)[0].lower()
    return owner_from_github_url(value)


def is_url_like(token: str) -> bool:
    return (
        token.startswith('http://')
        or token.startswith('https://')
        or token.startswith('ssh://')
        or token.startswith('git@')
        or '@github.com:' in token
    )


def strip_env_assignments(tokens):
    i = 0
    while i < len(tokens) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', tokens[i]):
        i += 1
    return tokens[i:]


def run_git(cwd: str, *args):
    try:
        result = subprocess.run(
            ['git', '-C', cwd, *args], capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def resolve_repo_owner(cwd: str):
    """Resolve the GitHub owner of `origin` for the repo at cwd, if any."""
    url = run_git(cwd, 'remote', 'get-url', 'origin')
    return owner_from_github_url(url) if url else None


def resolve_named_remote_owner(cwd: str, name: str):
    url = run_git(cwd, 'remote', 'get-url', name)
    return owner_from_github_url(url) if url else None


def find_git_violation(args, cwd: str, allowed_owners):
    i = 0
    while i < len(args) and args[i].startswith('-'):
        if args[i] == '-C' and i + 1 < len(args):
            i += 2
        else:
            i += 1
    args = args[i:]
    if not args:
        return None

    subcommand = args[0]
    rest = args[1:]

    if subcommand in GIT_SAFE_SUBCOMMANDS:
        return None

    owner = None

    if subcommand in GIT_URL_ARG_SUBCOMMANDS or subcommand == 'submodule':
        positionals = [a for a in rest if not a.startswith('-')]
        if subcommand == 'submodule':
            if not positionals or positionals[0] != 'add':
                return None
            positionals = positionals[1:]
        url = positionals[0] if positionals else None
        if url and is_url_like(url):
            owner = owner_from_github_url(url)
        else:
            return None

    elif subcommand == 'remote':
        positionals = [a for a in rest if not a.startswith('-')]
        if len(positionals) >= 3 and positionals[0] in ('add', 'set-url'):
            url = positionals[2]
            owner = owner_from_github_url(url) if is_url_like(url) else None
        else:
            return None

    elif subcommand in GIT_REMOTE_URL_SUBCOMMANDS:
        positionals = [a for a in rest if not a.startswith('-')]
        target = positionals[0] if positionals else None
        if target and is_url_like(target):
            owner = owner_from_github_url(target)
        elif target:
            owner = resolve_named_remote_owner(cwd, target)
        else:
            owner = resolve_repo_owner(cwd)

    else:
        owner = resolve_repo_owner(cwd)

    if owner and owner.lower() not in allowed_owners:
        return f"git {subcommand} targets github.com/{owner}"
    return None


def find_gh_violation(args, cwd: str, allowed_owners):
    for i, tok in enumerate(args):
        value = None
        if tok in ('-R', '--repo') and i + 1 < len(args):
            value = args[i + 1]
        elif tok.startswith('--repo='):
            value = tok[len('--repo='):]
        if value:
            owner = owner_from_owner_repo(value)
            if owner and owner not in allowed_owners:
                return f"gh --repo targets github.com/{owner}"
            return None

    if not args:
        return None
    subcommand = args[0]
    rest = args[1:]
    positionals = [a for a in rest if not a.startswith('-')]

    if subcommand in GH_SAFE_SUBCOMMANDS:
        return None

    if subcommand == 'repo':
        if not positionals:
            return None
        action = positionals[0]
        target = positionals[1] if len(positionals) > 1 else None
        if action in GH_REPO_TARGET_ACTIONS and target:
            owner = owner_from_owner_repo(target)
            if owner and owner not in allowed_owners:
                return f"gh repo {action} targets github.com/{owner}"
        elif action == 'create' and target and '/' in target:
            owner = owner_from_owner_repo(target)
            if owner and owner not in allowed_owners:
                return f"gh repo create targets github.com/{owner}"
        return None

    if subcommand == 'api':
        path = positionals[0] if positionals else None
        if path:
            match = API_REPOS_PATH_RE.search(path)
            if match:
                owner = match.group(1).lower()
                if owner not in allowed_owners:
                    return f"gh api targets github.com/{owner}"
        return None

    owner = resolve_repo_owner(cwd)
    if owner and owner not in allowed_owners:
        return f"gh {subcommand} targets github.com/{owner}"
    return None


def find_scope_violation(command: str, cwd: str, allowed_owners):
    """Return a human-readable violation reason, or None if the command is fine."""
    for raw_segment in SEGMENT_SPLIT_RE.split(command):
        segment = raw_segment.strip()
        if not segment or ('git' not in segment and 'gh' not in segment):
            continue

        try:
            tokens = shlex.split(segment)
        except ValueError:
            # Segment mentions git/gh but doesn't tokenize cleanly (e.g. an
            # unbalanced quote). Fail closed rather than silently skipping it.
            return (
                f"a command segment could not be safely parsed ({segment!r}), "
                "which may target an owner outside the allowed owner(s) "
                f"({', '.join(sorted(allowed_owners))})."
            )

        tokens = strip_env_assignments(tokens)
        if not tokens:
            continue

        if tokens[0] == 'git':
            reason = find_git_violation(tokens[1:], cwd, allowed_owners)
        elif tokens[0] == 'gh':
            reason = find_gh_violation(tokens[1:], cwd, allowed_owners)
        else:
            continue

        if reason:
            return (
                f"{reason}, which is outside the allowed owner(s) "
                f"({', '.join(sorted(allowed_owners))})."
            )

    return None


def main():
    import json
    import os

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    command = input_data.get('tool_input', {}).get('command', '') or ''
    if not command or ('git' not in command and 'gh' not in command):
        sys.exit(0)

    cwd = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    allowed_owners = get_allowed_git_owners()

    try:
        violation = find_scope_violation(command, cwd, allowed_owners)
    except Exception as exc:
        print(f"🚫 BLOCKED - repo-scope-guard failed to analyze this command safely: {exc}",
              file=sys.stderr)
        sys.exit(2)

    if violation:
        print(f"🚫 BLOCKED - {violation}", file=sys.stderr)
        print("This command was blocked by the repo-scope-guard hook.", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
