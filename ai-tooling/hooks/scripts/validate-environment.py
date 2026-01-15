#!/usr/bin/env python3
"""
SessionStart hook - Validates environment on session startup.
Checks for required tools, configuration, and potential issues.

Source: https://github.com/CloudAI-X/claude-workflow
"""
import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from base_hook import BaseHook


class ValidateEnvironmentHook(BaseHook):
    """Hook to validate environment on session start."""

    def __init__(self):
        super().__init__('validate-environment')

    def execute(self) -> int:
        info, warnings = self.check_environment()

        if info:
            print("Environment check:")
            for item in info:
                print(f"  ✓ {item}")

        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")

        return 0

    def check_environment(self):
        """Check for required tools and configuration."""
        warnings = []
        info = []

        if shutil.which("node"):
            info.append("Node.js available")
        else:
            warnings.append("Node.js not found - npm commands may fail")

        if shutil.which("python3"):
            info.append("Python 3 available")
        else:
            warnings.append("Python 3 not found - some hooks may fail")

        if shutil.which("git"):
            info.append("Git available")
        else:
            warnings.append("Git not found - version control commands unavailable")

        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        env_example = project_dir / ".env.example"
        env_file = project_dir / ".env"

        if env_example.exists() and not env_file.exists():
            warnings.append("No .env file found but .env.example exists - copy and configure it")

        package_json = project_dir / "package.json"
        if package_json.exists():
            node_modules = project_dir / "node_modules"
            if not node_modules.exists():
                warnings.append("node_modules not found - run 'npm install' first")

        return info, warnings


if __name__ == "__main__":
    ValidateEnvironmentHook().run()
