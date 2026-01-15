#!/usr/bin/env python3
"""
Protect sensitive files from modification.
Blocks edits to production configs, lock files, and sensitive directories.

Original Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook
from config import get_protected_patterns
from pattern_matcher import matches_pattern


class ProtectFilesHook(BaseHook):
    """Hook to protect sensitive files from modification."""

    def __init__(self):
        super().__init__('protect-files')
        self.blocked_patterns, self.warn_patterns = get_protected_patterns()

    def execute(self) -> int:
        file_path = self.get_file_path()

        if not file_path:
            return 0

        blocked = matches_pattern(file_path, self.blocked_patterns)
        if blocked:
            print(f"🚫 BLOCKED: {file_path}")
            print(f"   Matches protected pattern: {blocked}")
            print("   Use --force if this is intentional")
            return 2

        warned = matches_pattern(file_path, self.warn_patterns)
        if warned:
            print(f"⚠️ WARNING: Editing sensitive file: {file_path}")
            print(f"   Matches pattern: {warned}")

        return 0


if __name__ == '__main__':
    ProtectFilesHook().run()
