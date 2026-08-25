"""Cross-process locking for GitHub App token refreshes."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


DEFAULT_LOCK_PATH = (
    Path.home() / 'Library' / 'Caches' / 'machine-setup' / 'refresh-gh-token.lock'
)


@contextmanager
def gh_token_refresh_lock(lock_path: Optional[Path] = None) -> Iterator[None]:
    path = DEFAULT_LOCK_PATH if lock_path is None else Path(lock_path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, 'r+') as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
