#!/usr/bin/env python3
"""
Pre-commit security check hook.
Blocks commits that might contain secrets or security issues.

Original Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
import re
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook
from config import get_secret_patterns, get_security_reminders
from pattern_matcher import is_test_file, normalize_file_path


class SecurityCheckHook(BaseHook):
    """Hook to check for secrets and security issues."""

    def __init__(self):
        super().__init__('security-check')
        self.secret_patterns, self.skip_files = get_secret_patterns()
        self.security_reminders = get_security_reminders()

    def execute(self) -> int:
        file_path = self.get_file_path()
        content = self.get_content()

        if not file_path:
            return 0

        issues = self.check_for_secrets(content, file_path) if content else []
        reminders = self.check_for_reminders(file_path, content)

        if issues:
            print(f"🚫 BLOCKED - Security issue detected in {file_path}:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nThis edit has been BLOCKED to prevent committing secrets.")
            print("If this is a false positive, review and adjust patterns in hooks/lib/config.py")
            return 2

        if reminders:
            for reminder in reminders:
                print(f"⚠️ {reminder}", file=sys.stderr)

        return 0

    def check_for_secrets(self, content: str, file_path: str):
        """Check content for potential secrets."""
        issues = []

        if os.path.basename(file_path) in self.skip_files:
            return issues

        if is_test_file(file_path):
            return issues

        for pattern, secret_type in self.secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(f"Potential {secret_type} detected")

        return issues

    def check_for_reminders(self, file_path: str, content: str):
        """Check for non-blocking security reminders."""
        reminders = []
        normalized_path = normalize_file_path(file_path)

        for rule in self.security_reminders:
            path_substrings = rule.get('path_substrings', [])
            path_suffixes = rule.get('path_suffixes', [])
            substrings = rule.get('substrings', [])

            if path_substrings:
                if any(substring in normalized_path for substring in path_substrings):
                    if not path_suffixes or any(
                        normalized_path.endswith(suffix) for suffix in path_suffixes
                    ):
                        reminders.append(rule['reminder'])
                        continue

            if content and substrings:
                if any(substring in content for substring in substrings):
                    reminders.append(rule['reminder'])

        return reminders


if __name__ == "__main__":
    SecurityCheckHook().run()
