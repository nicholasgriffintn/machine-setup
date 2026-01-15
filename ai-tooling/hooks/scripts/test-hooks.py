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

    print("\n" + "=" * 60)
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(tests)} tests")

    if failed == 0:
        print("✅ All hooks are working correctly!\n")
        return 0
    else:
        print(f"⚠️  {failed} hook(s) need attention\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
