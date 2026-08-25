#!/usr/bin/env python3
"""
Test script to validate hooks are working correctly.
Run this to verify hook configuration and functionality.
"""
import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PLUGIN_ROOT = HOOKS_DIR.parent
AI_TOOLING_DIR = PLUGIN_ROOT.parent
CLAUDE_SETTINGS = AI_TOOLING_DIR / 'claude-settings.json'
CODEX_HOOKS = AI_TOOLING_DIR / 'codex-hooks.json'

# Harness-specific home-dir prefixes that hook commands use to invoke
# scripts. Normalizing these out is what lets the two hand-maintained
# settings files be compared for drift below.
HARNESS_PREFIXES = ('~/.claude/', '~/.codex/')


def test_hook(hook_name, test_input):
    """Test a hook with given input."""
    hook_path = HOOKS_DIR / f"{hook_name}.py"

    if not hook_path.exists():
        return False, f"Hook not found: {hook_path}"

    try:
        result = subprocess.run(
            ['python3', str(hook_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=5
        )

        return True, {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return False, str(e)


def _normalize_hook_wiring(hooks_block):
    """Strip the harness home-dir prefix from every hook command so wiring
    can be compared across claude-settings.json and codex-hooks.json."""
    normalized = {}
    for event, matchers in hooks_block.items():
        norm_matchers = []
        for matcher_entry in matchers:
            norm_hooks = []
            for hook in matcher_entry.get('hooks', []):
                command = hook.get('command', '')
                for prefix in HARNESS_PREFIXES:
                    command = command.replace(prefix, '~/<harness>/')
                norm_hooks.append({
                    'type': hook.get('type'),
                    'command': command,
                    'timeout': hook.get('timeout'),
                })
            norm_matchers.append({
                'matcher': matcher_entry.get('matcher'),
                'hooks': norm_hooks,
            })
        normalized[event] = norm_matchers
    return normalized


def check_hook_parity():
    """Diff claude-settings.json and codex-hooks.json hook wiring, modulo the
    ~/.claude/ vs ~/.codex/ home-dir prefix.

    These two files hand-duplicate the same matchers/scripts/timeouts with no
    generator keeping them in lockstep, so this catches an event edited in
    one file and forgotten in the other. Events that only exist in one file
    (e.g. a harness without an equivalent hook type) are reported but not
    treated as a failure -- only mismatches within events both files define
    are.
    """
    if not CLAUDE_SETTINGS.is_file() or not CODEX_HOOKS.is_file():
        return False, f"Missing {CLAUDE_SETTINGS} or {CODEX_HOOKS}"

    with open(CLAUDE_SETTINGS) as f:
        claude_hooks = _normalize_hook_wiring(json.load(f).get('hooks', {}))
    with open(CODEX_HOOKS) as f:
        codex_hooks = _normalize_hook_wiring(json.load(f).get('hooks', {}))

    shared = sorted(set(claude_hooks) & set(codex_hooks))
    only_claude = sorted(set(claude_hooks) - set(codex_hooks))
    only_codex = sorted(set(codex_hooks) - set(claude_hooks))

    diverged = [event for event in shared if claude_hooks[event] != codex_hooks[event]]

    notes = []
    if only_claude:
        notes.append(f"events only in claude-settings.json: {only_claude}")
    if only_codex:
        notes.append(f"events only in codex-hooks.json: {only_codex}")

    if diverged:
        detail = f"Hook wiring diverged for shared event(s) {diverged}"
        if notes:
            detail += " (" + '; '.join(notes) + ")"
        return False, detail

    message = "Shared hook wiring matches modulo home-dir prefix"
    if notes:
        message += " (" + '; '.join(notes) + ")"
    return True, message


def main():
    """Run hook tests."""
    print("🧪 Testing Claude Code Hooks\n")
    print("=" * 60)

    tests = [
        {
            'name': 'protect-files (allowed file)',
            'hook': 'protect-files',
            'input': {'tool_input': {'file_path': 'src/app.py'}},
            'expected_exit': 0
        },
        {
            'name': 'protect-files (blocked file)',
            'hook': 'protect-files',
            'input': {'tool_input': {'file_path': '.env'}},
            'expected_exit': 2
        },
        {
            'name': 'security-check (clean content)',
            'hook': 'security-check',
            'input': {
                'tool_input': {
                    'file_path': 'config.py',
                    'content': 'API_KEY = "placeholder"\n'
                }
            },
            'expected_exit': 0
        },
        {
            'name': 'security-check (API key detected)',
            'hook': 'security-check',
            'input': {
                'tool_input': {
                    'file_path': 'config.py',
                    'content': 'API_KEY = sk-' + 'a' * 48 + '\n'
                }
            },
            'expected_exit': 2
        },
        {
            'name': 'security-check (MultiEdit secret detected)',
            'hook': 'security-check',
            'input': {
                'tool_input': {
                    'file_path': 'config.py',
                    'edits': [
                        {'new_string': 'API_KEY = sk-' + 'a' * 48 + '\n'}
                    ]
                }
            },
            'expected_exit': 2
        },
        {
            'name': 'format-on-edit',
            'hook': 'format-on-edit',
            'input': {'tool_input': {'file_path': 'test.py'}},
            'expected_exit': 0
        },
        {
            'name': 'validate-environment',
            'hook': 'validate-environment',
            'input': {},
            'expected_exit': 0
        },
        {
            'name': 'validate-prompt (normal prompt)',
            'hook': 'validate-prompt',
            'input': {'prompt': 'Help me write a function'},
            'expected_exit': 0
        },
        {
            'name': 'log-commands',
            'hook': 'log-commands',
            'input': {
                'tool_input': {
                    'command': 'ls -la',
                    'description': 'List files'
                }
            },
            'expected_exit': 0
        },
        {
            'name': 'repo-scope-guard (non-git command)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {'command': 'ls -la'}},
            'expected_exit': 0
        },
        {
            'name': 'repo-scope-guard (git clone own org)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {
                'command': 'git clone https://github.com/nicholasgriffintn/foo.git'
            }},
            'expected_exit': 0
        },
        {
            'name': 'repo-scope-guard (git clone other org, blocked)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {
                'command': 'git clone https://github.com/facebook/react.git'
            }},
            'expected_exit': 2
        },
        {
            'name': 'repo-scope-guard (git remote add other org, blocked)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {
                'command': 'git remote add upstream https://github.com/oven-sh/bun.git'
            }},
            'expected_exit': 2
        },
        {
            'name': 'repo-scope-guard (gh -R other org, blocked)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {
                'command': 'gh pr list -R facebook/react'
            }},
            'expected_exit': 2
        },
        {
            'name': 'repo-scope-guard (gh repo clone own org)',
            'hook': 'repo-scope-guard',
            'input': {'tool_input': {
                'command': 'gh repo clone nicholasgriffintn/foo'
            }},
            'expected_exit': 0
        },
    ]

    passed = 0
    failed = 0

    for test in tests:
        print(f"\n📋 Test: {test['name']}")
        print(f"   Hook: {test['hook']}")

        success, result = test_hook(test['hook'], test['input'])

        if not success:
            print(f"   ❌ FAILED: {result}")
            failed += 1
            continue

        if result['exit_code'] == test['expected_exit']:
            print(f"   ✅ PASSED (exit code: {result['exit_code']})")
            if result['stdout']:
                print(f"   Output: {result['stdout'].strip()[:100]}")
            passed += 1
        else:
            print(f"   ❌ FAILED: Expected exit {test['expected_exit']}, got {result['exit_code']}")
            if result['stderr']:
                print(f"   Error: {result['stderr'].strip()}")
            failed += 1

    print(f"\n📋 Test: claude-settings.json / codex-hooks.json parity")
    parity_ok, parity_message = check_hook_parity()
    if parity_ok:
        print(f"   ✅ PASSED: {parity_message}")
        passed += 1
    else:
        print(f"   ❌ FAILED: {parity_message}")
        failed += 1
    total_tests = len(tests) + 1

    print("\n" + "=" * 60)
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {total_tests} tests")

    if failed == 0:
        print("✅ All hooks are working correctly!\n")
        return 0
    else:
        print(f"⚠️  {failed} hook(s) need attention\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
