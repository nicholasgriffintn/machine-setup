#!/usr/bin/env python3
"""
Base hook class for all Python hooks.
Provides common functionality: JSON parsing, error handling, logging.
"""
import json
import sys
import os
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class BaseHook(ABC):
    """Base class for all Python hooks."""

    def __init__(self, hook_name: str):
        self.hook_name = hook_name
        self.input_data: Dict[str, Any] = {}
        self.exit_code = 0

    def run(self):
        """Main entry point - handles common logic."""
        try:
            self.input_data = json.load(sys.stdin)
            self.exit_code = self.execute()
        except Exception as e:
            self.handle_error(e)
        finally:
            sys.exit(self.exit_code)

    @abstractmethod
    def execute(self) -> int:
        """Hook-specific logic. Returns exit code (0=continue, 1=error, 2=block)."""
        pass

    def handle_error(self, error: Exception):
        """Log error and exit gracefully."""
        self.log_error(f"ERROR: {type(error).__name__}: {str(error)}")
        self.exit_code = 0

    def log_error(self, message: str):
        """Log message to hook log file."""
        try:
            log_dir = Path(os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())) / '.claude'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'hooks.log'
            with open(log_file, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] [{self.hook_name}] {message}\n")
        except Exception:
            pass

    def get_file_path(self) -> Optional[str]:
        """Extract file_path from tool_input."""
        return self.input_data.get('tool_input', {}).get('file_path', '')

    def get_content(self) -> Optional[str]:
        """Extract content from tool_input."""
        tool_input = self.input_data.get('tool_input', {})
        content = tool_input.get('content', '')
        if content:
            return content
        new_string = tool_input.get('new_string', '')
        if new_string:
            return new_string
        edits = tool_input.get('edits', [])
        if edits:
            return ' '.join(edit.get('new_string', '') for edit in edits)
        return ''

    def get_command(self) -> Optional[str]:
        """Extract command from tool_input."""
        return self.input_data.get('tool_input', {}).get('command', '')

    def get_prompt(self) -> Optional[str]:
        """Extract prompt from input."""
        return self.input_data.get('prompt', '')
