#!/usr/bin/env python3
"""
PreToolUse hook (Bash matcher) that scopes both the `git` and `gh` CLIs to
an allow-list of GitHub owners/orgs (see lib/config.py: get_allowed_git_owners).

This is a defense-in-depth layer, not the only one: claude-settings.json also
sets `url.https://github.com/.insteadOf git@github.com:` (and the ssh:// form)
so every AI-driven github.com push goes out over HTTPS, where
git-credential-clanker.py hands out a token scoped to a single owner's App
installation -- meaning even a command this guard fails to parse still can't
authenticate against a different owner's repo over SSH with the user's own key.

Fails CLOSED on an unexpected internal error (blocks rather than silently
allowing the command through), unlike BaseHook's default fail-open handling,
since a guard that fails open on its own bugs isn't a guard.
"""
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from config import get_allowed_git_owners  # noqa: E402

SEGMENT_SPLIT_RE = re.compile(r'&&|\|\||[;|\n]')
# Strip subshell/brace-group/command-substitution wrapping (e.g. `(git ...)`,
# `{ git ...; }`, `` `git ...` ``, `$(git ...)`) from segment boundaries so
# wrapped invocations still surface `git`/`gh` as the first token instead of
# silently skipping scope checks. Only the outer boundary is touched, so this
# never reaches into quoted arguments (e.g. a commit message like "fix (bug)").
LEADING_WRAP_RE = re.compile(r'^[(){}$`]+\s*')
TRAILING_WRAP_RE = re.compile(r'\s*[(){}`]+$')
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

# Wrapping git/gh in one of these (`bash -c "git push ..."`, or invoking
# `/usr/bin/git` instead of bare `git`) must not skip scope checking.
SHELL_WRAPPER_BASENAMES = {'bash', 'sh', 'zsh', 'dash'}
MAX_RECURSION_DEPTH = 5


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
        if not path:
            return "gh api with no path is not owner-scoped"

        normalized = path.strip().lstrip('/')
        first_segment = normalized.split('?', 1)[0].split('/', 1)[0].lower()
        if first_segment == 'graphql':
            # GraphQL has no owner in the URL, so it can reach any repo/org
            # visible to the token regardless of path scoping. Hard-block it.
            return "gh api graphql is not owner-scoped and is blocked"

        match = API_REPOS_PATH_RE.search(path)
        if match:
            owner = match.group(1).lower()
            if owner not in allowed_owners:
                return f"gh api targets github.com/{owner}"
            return None

        # Default deny: any path we don't recognize as repos/<owner>/...
        # is not owner-scoped (e.g. orgs/<org>/repos, /user, /installation/*).
        return f"gh api path '{path}' is not a recognized repos/<owner>/... path"

    owner = resolve_repo_owner(cwd)
    if owner and owner not in allowed_owners:
        return f"gh {subcommand} targets github.com/{owner}"
    return None


def find_scope_violation(command: str, cwd: str, allowed_owners, _depth: int = 0):
    """Return a human-readable violation reason, or None if the command is fine."""
    if _depth > MAX_RECURSION_DEPTH:
        return "command nesting too deep to analyze safely"

    for raw_segment in SEGMENT_SPLIT_RE.split(command):
        segment = raw_segment.strip()
        segment = LEADING_WRAP_RE.sub('', segment)
        segment = TRAILING_WRAP_RE.sub('', segment)
        if not segment or ('git' not in segment and 'gh' not in segment):
            continue

        try:
            tokens = shlex.split(segment)
        except ValueError:
            continue

        tokens = strip_env_assignments(tokens)
        if not tokens:
            continue

        # `env` just strips leading VAR=val assignments (already handled
        # above) and optional flags before the real command.
        while tokens and Path(tokens[0]).name == 'env':
            tokens = tokens[1:]
            while tokens and tokens[0].startswith('-'):
                tokens = tokens[1:]
            tokens = strip_env_assignments(tokens)

        if not tokens:
            continue

        basename = Path(tokens[0]).name

        if basename in SHELL_WRAPPER_BASENAMES:
            if '-c' in tokens:
                wrapped = tokens[tokens.index('-c') + 1:]
                if wrapped:
                    reason = find_scope_violation(
                        ' '.join(shlex.quote(t) for t in wrapped)
                        if len(wrapped) > 1 else wrapped[0],
                        cwd, allowed_owners, _depth + 1,
                    )
                    if reason:
                        return reason
            continue

        if basename == 'git':
            reason = find_git_violation(tokens[1:], cwd, allowed_owners)
        elif basename == 'gh':
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
