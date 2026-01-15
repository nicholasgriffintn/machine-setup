#!/usr/bin/env python3
"""Pattern matching utilities for hooks."""
import os
import fnmatch
from typing import List, Optional


def normalize_file_path(file_path: str) -> str:
    """Normalize file path to prevent traversal attacks."""
    file_path = os.path.normpath(file_path)
    # Remove leading './' but preserve leading '.' for dotfiles
    if file_path.startswith('./'):
        file_path = file_path[2:]
    # Remove absolute path prefix
    file_path = file_path.lstrip('/')
    return file_path


def matches_pattern(file_path: str, patterns: List[str]) -> Optional[str]:
    """Check if file path matches any pattern."""
    file_path = normalize_file_path(file_path)

    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return pattern
        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return pattern

    return None


def is_test_file(file_path: str) -> bool:
    """Check if file is a test file."""
    normalized_path = normalize_file_path(file_path).lower()
    parts = normalized_path.split(os.sep)
    basename = os.path.basename(normalized_path)

    if any(part in ('test', 'tests', '__tests__', 'spec', 'specs') for part in parts):
        return True

    if basename.startswith('test_'):
        return True

    if basename.endswith(('_test', '_spec')):
        return True

    if '.test.' in basename or '.spec.' in basename:
        return True

    return False
