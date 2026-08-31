#!/usr/bin/env python3
"""
Block code comments from being added.

Two gates:
  PreToolUse  Edit|Write|MultiEdit  - refuses a write that introduces comment lines
  PreToolUse  Bash (git commit)     - refuses a commit whose diff adds comment lines
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook

SLASH_EXTS = {
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts',
    '.swift', '.go', '.rs', '.java', '.kt', '.kts', '.scala', '.dart',
    '.c', '.h', '.cc', '.cpp', '.hpp', '.m', '.mm', '.cs',
    '.php', '.css', '.scss', '.less', '.proto', '.gradle', '.groovy',
}
HASH_EXTS = {'.py', '.rb', '.sh', '.bash', '.zsh', '.fish', '.pl', '.r', '.ex', '.exs', '.jl'}
DASH_EXTS = {'.sql', '.lua', '.hs', '.elm'}

SKIP_PATH_PARTS = ('/node_modules/', '/dist/', '/build/', '/.git/', '/vendor/', '/.claude/')

ALLOWED = (
    'eslint', 'oxlint', 'oxfmt', 'biome', 'prettier-ignore', 'stylelint', 'deno-lint',
    '@ts-', 'ts-expect-error', 'ts-ignore', 'noqa', 'type: ignore', 'pylint', 'pyright',
    'mypy', 'ruff', 'swiftlint', 'go:generate', 'go:build', '+build', 'coding:',
    'istanbul ignore', 'c8 ignore', 'v8 ignore', 'sourcemappingurl', 'spdx',
    'copyright', 'licensed under', '@vite-ignore', '@vitest-environment', 'shellcheck',
)

SLASH_START = re.compile(r'^(//|/\*|\*/|\*(\s|$))')
CD_PREFIX = re.compile(r"""\s*cd\s+(?P<path>"[^"]+"|'[^']+'|[^\s;&|]+)""")


def comment_markers(path):
    suffix = Path(path).suffix.lower()
    if any(part in path.replace('\\', '/') for part in SKIP_PATH_PARTS):
        return None
    if suffix in SLASH_EXTS:
        return 'slash'
    if suffix in HASH_EXTS:
        return 'hash'
    if suffix in DASH_EXTS:
        return 'dash'
    return None


def is_comment(line, kind):
    stripped = line.strip()
    if not stripped:
        return False
    if kind == 'slash':
        if not SLASH_START.match(stripped):
            return False
    elif kind == 'hash':
        if not stripped.startswith('#') or stripped.startswith('#!'):
            return False
    elif kind == 'dash':
        if not stripped.startswith('--'):
            return False
    else:
        return False
    lowered = stripped.lower()
    return not any(token in lowered for token in ALLOWED)


def comment_lines(text, kind):
    return [line.strip() for line in text.splitlines() if is_comment(line, kind)]


def added_comments(old_text, new_text, kind):
    before = comment_lines(old_text, kind)
    added = []
    for line in comment_lines(new_text, kind):
        if line in before:
            before.remove(line)
        else:
            added.append(line)
    return added


def report(findings):
    out = sys.stderr
    print("🚫 BLOCKED - this adds code comments, which you never write.", file=out)
    for location, line in findings:
        print(f"  {location}: {line}", file=out)
    print("\nDelete them. If the code needs a paragraph to explain it, rename or", file=out)
    print("restructure it instead. Durable reasoning belongs in the commit message,", file=out)
    print("the PR body, or an ADR - never inline.", file=out)
    return 2


class NoCommentsGuard(BaseHook):

    def __init__(self):
        super().__init__('no-comments-guard')

    def execute(self) -> int:
        tool = self.input_data.get('tool_name', '')
        if tool == 'Bash':
            return self.check_commit()
        if tool in ('Edit', 'Write', 'MultiEdit'):
            return self.check_write()
        return 0

    def check_write(self) -> int:
        file_path = self.get_file_path()
        kind = comment_markers(file_path) if file_path else None
        if not kind:
            return 0

        tool_input = self.input_data.get('tool_input', {})
        edits = tool_input.get('edits')
        if edits:
            pairs = [(e.get('old_string', ''), e.get('new_string', '')) for e in edits]
        elif 'new_string' in tool_input:
            pairs = [(tool_input.get('old_string', ''), tool_input.get('new_string', ''))]
        else:
            existing = ''
            try:
                existing = Path(file_path).read_text()
            except OSError:
                pass
            pairs = [(existing, tool_input.get('content', ''))]

        findings = []
        for old_text, new_text in pairs:
            for line in added_comments(old_text, new_text, kind):
                findings.append((Path(file_path).name, line))

        return report(findings) if findings else 0

    def check_commit(self) -> int:
        command = self.get_command() or ''
        if not re.search(r'\bgit\b[^|;&]*\bcommit\b', command):
            return 0

        ranges = ['--cached']
        if re.search(r'\bcommit\b[^|;&]*\s-[a-zA-Z]*a', command):
            ranges.append('HEAD')

        workdir = self.command_workdir(command)

        findings = []
        for target in ranges:
            findings.extend(self.diff_comments(target, workdir))

        return report(findings) if findings else 0

    def command_workdir(self, command):
        match = re.match(CD_PREFIX, command)
        if not match:
            return self.input_data.get('cwd') or None
        path = match.group('path').strip('"').strip("'")
        expanded = Path(path).expanduser()

        return str(expanded) if expanded.is_dir() else None

    def diff_comments(self, target, workdir=None):
        try:
            diff = subprocess.run(
                ['git', 'diff', '-U0', target],
                capture_output=True, text=True, timeout=20, cwd=workdir,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if diff.returncode != 0:
            return []

        findings = []
        path, kind, lineno = None, None, 0
        for raw in diff.stdout.splitlines():
            if raw.startswith('+++ b/'):
                path = raw[6:]
                kind = comment_markers(path)
            elif raw.startswith('@@'):
                match = re.search(r'\+(\d+)', raw)
                lineno = int(match.group(1)) if match else 0
            elif raw.startswith('+') and not raw.startswith('+++'):
                if kind and is_comment(raw[1:], kind):
                    findings.append((f"{path}:{lineno}", raw[1:].strip()))
                lineno += 1
        return findings


if __name__ == '__main__':
    NoCommentsGuard().run()
