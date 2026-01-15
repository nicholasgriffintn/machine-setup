#!/usr/bin/env python3
"""
Auto-format files after Claude edits them.
Detects file type and runs appropriate formatter.

Original Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
import os
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook
from config import get_formatters


class FormatOnEditHook(BaseHook):
    """Hook to auto-format files after editing."""

    def __init__(self):
        super().__init__('format-on-edit')
        self.formatters = get_formatters()

    def execute(self) -> int:
        file_path = self.get_file_path()

        if not file_path or not os.path.exists(file_path):
            return 0

        ext = os.path.splitext(file_path)[1].lower()
        formatter_config = self.formatters.get(ext)

        if not formatter_config:
            return 0

        command = formatter_config.get('command', [])
        timeout = formatter_config.get('timeout', 10)

        if not command:
            return 0

        formatter_bin = command[0]
        if not shutil.which(formatter_bin):
            return 0

        try:
            cmd = command + [file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                text=True
            )

            if result.returncode != 0 and result.stderr:
                self.log_error(f"Formatter failed for {file_path}: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.log_error(f"Formatter timeout for {file_path}")
        except Exception as e:
            self.log_error(f"Formatter error for {file_path}: {str(e)}")

        return 0


if __name__ == '__main__':
    FormatOnEditHook().run()
