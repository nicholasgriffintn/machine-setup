#!/usr/bin/env python3
"""
UserPromptSubmit hook - Validates user prompts before processing.
Can provide warnings or context to Claude based on the prompt content.

Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook
from config import get_agent_hints


class ValidatePromptHook(BaseHook):
    """Hook to validate user prompts and provide helpful hints."""

    def __init__(self):
        super().__init__('validate-prompt')
        self.agent_hints, self.dangerous_patterns = get_agent_hints()
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.compiled_hints = {
            re.compile(pattern, re.IGNORECASE): hint
            for pattern, hint in self.agent_hints.items()
        }
        self.compiled_dangerous = [
            (re.compile(pattern, re.IGNORECASE), warning)
            for pattern, warning in self.dangerous_patterns
        ]

    def execute(self) -> int:
        prompt = self.get_prompt()

        if not prompt:
            return 0

        messages = self.validate_prompt(prompt)

        for msg in messages:
            print(msg)

        return 0

    def validate_prompt(self, prompt: str):
        """Validate the user prompt and provide helpful context."""
        messages = []

        for pattern, hint in self.compiled_hints.items():
            if pattern.search(prompt):
                messages.append(hint)
                break

        for pattern, warning in self.compiled_dangerous:
            if pattern.search(prompt):
                messages.append(warning)

        return messages


if __name__ == "__main__":
    ValidatePromptHook().run()
