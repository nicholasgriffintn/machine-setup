#!/usr/bin/env python3
"""
Auto-format files after Claude edits them.
Detects file type and runs appropriate formatter.

Original Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook
from formatter_detection import detect_formatter, find_repository_root, resolve_file_path


class FormatOnEditHook(BaseHook):
    """Hook to auto-format files after editing."""

    def __init__(self):
        super().__init__('format-on-edit')

    def execute(self) -> int:
        file_path = self.get_file_path()

        if not file_path:
            return 0

        project_dir = os.environ.get('CLAUDE_PROJECT_DIR') or os.environ.get('CODEX_PROJECT_DIR')
        resolved_file = resolve_file_path(file_path, project_dir)
        if not resolved_file.is_file():
            return 0

        repository_root = find_repository_root(resolved_file, project_dir)
        if not repository_root:
            return 0

        formatter = detect_formatter(resolved_file, repository_root)
        if not formatter:
            return 0

        try:
            result = subprocess.run(
                formatter.args,
                capture_output=True,
                timeout=formatter.timeout,
                text=True,
                cwd=formatter.cwd,
            )

            if result.returncode != 0 and result.stderr:
                self.log_error(f"Formatter failed for {resolved_file}: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.log_error(f"Formatter timeout for {resolved_file}")
        except Exception as e:
            self.log_error(f"Formatter error for {resolved_file}: {str(e)}")

        return 0


if __name__ == '__main__':
    FormatOnEditHook().run()
