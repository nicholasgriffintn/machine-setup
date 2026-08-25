#!/usr/bin/env python3
"""Ensure existing zsh installations resolve machine-setup shims first."""

import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.secure_io import write_text_atomic  # noqa: E402


START_MARKER = '# >>> machine-setup local bin >>>'
PATH_BLOCK = f'''{START_MARKER}
typeset -U path PATH
path=("$HOME/.local/bin" $path)
# <<< machine-setup local bin <<<'''


def ensure_local_bin_path(zshrc_path: Path) -> bool:
    if not zshrc_path.is_file():
        return False

    existing = zshrc_path.read_text()
    if START_MARKER in existing:
        return False

    separator = '' if existing.endswith('\n') else '\n'
    updated = f'{existing}{separator}\n{PATH_BLOCK}\n'
    mode = stat.S_IMODE(zshrc_path.stat().st_mode)
    write_text_atomic(zshrc_path, updated, mode)
    return True


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / '.zshrc'
    state = 'Updated' if ensure_local_bin_path(target) else 'Already up to date'
    print(f'{state}: {target} [machine-setup local bin]')


if __name__ == '__main__':
    main()
