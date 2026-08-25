#!/usr/bin/env python3
"""
~/.codex/config.toml is Codex's own live app-state file (project trust
list, per-hook consent tracking) as well as user config, so it can't be
symlinked from this repo like the rest of ai-tooling -- that would mean
every project Codex trusts gets written straight into this git repo.

Instead this keeps just the [shell_environment_policy.set] table in
lockstep with claude-settings.json's "env" block (the single source of
truth for both harnesses), rewriting only that section and leaving
everything else in config.toml untouched.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLAUDE_SETTINGS = REPO_ROOT / 'ai-tooling' / 'claude-settings.json'
CODEX_CONFIG = Path.home() / '.codex' / 'config.toml'
SECTION_HEADER = '[shell_environment_policy.set]'


def load_desired_env():
    with open(CLAUDE_SETTINGS) as f:
        env = json.load(f).get('env', {})
    return {k: v.replace('~/.claude/', '~/.codex/') if isinstance(v, str) else v
            for k, v in env.items()}


def toml_line(key, value):
    return f"{key} = {json.dumps(str(value))}"


def sync(desired, config_path):
    if not config_path.is_file():
        print(f"No Codex config at {config_path}, skipping", file=sys.stderr)
        return False

    lines = config_path.read_text().splitlines()

    section_start = next(
        (i for i, line in enumerate(lines) if line.strip() == SECTION_HEADER), None
    )

    if section_start is None:
        new_lines = lines + ['', SECTION_HEADER] + [toml_line(k, v) for k, v in desired.items()]
        changed = True
    else:
        section_end = len(lines)
        for i in range(section_start + 1, len(lines)):
            if re.match(r'^\s*\[', lines[i]):
                section_end = i
                break

        section_lines = lines[section_start + 1:section_end]
        existing_keys = {}
        for i, line in enumerate(section_lines):
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=', line)
            if match:
                existing_keys[match.group(1)] = i

        changed = False
        for key, value in desired.items():
            new_line = toml_line(key, value)
            if key in existing_keys:
                idx = existing_keys[key]
                if section_lines[idx] != new_line:
                    section_lines[idx] = new_line
                    changed = True
            else:
                section_lines.append(new_line)
                changed = True

        new_lines = lines[:section_start + 1] + section_lines + lines[section_end:]

    if changed:
        config_path.write_text('\n'.join(new_lines) + '\n')
    return changed


def main():
    desired = load_desired_env()
    changed = sync(desired, CODEX_CONFIG)
    state = 'Updated' if changed else 'Already up to date'
    print(f"{state}: {CODEX_CONFIG} [shell_environment_policy.set]")


if __name__ == '__main__':
    main()
