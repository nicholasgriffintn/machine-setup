#!/usr/bin/env python3
"""
Log all bash commands executed by Claude for auditing.

Original Source: https://github.com/CloudAI-X/claude-workflow
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

def main():
    try:
        input_data = json.load(sys.stdin)
        command = input_data.get('tool_input', {}).get('command', '')
        description = input_data.get('tool_input', {}).get('description', 'No description')

        if not command:
            sys.exit(0)

        log_dir = Path(os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())) / '.claude'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'command-history.log'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {command}\n")
            if description and description != 'No description':
                f.write(f"  Description: {description}\n")

    except Exception:
        pass

    sys.exit(0)

if __name__ == '__main__':
    main()
