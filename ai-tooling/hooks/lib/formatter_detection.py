#!/usr/bin/env python3
"""Detect repository-owned formatters for edited files."""
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


PRETTIER_CONFIG_FILES = (
    '.prettierrc',
    '.prettierrc.json',
    '.prettierrc.json5',
    '.prettierrc.yaml',
    '.prettierrc.yml',
    '.prettierrc.toml',
    '.prettierrc.js',
    '.prettierrc.cjs',
    '.prettierrc.mjs',
    '.prettierrc.ts',
    '.prettierrc.cts',
    '.prettierrc.mts',
    'prettier.config.js',
    'prettier.config.cjs',
    'prettier.config.mjs',
    'prettier.config.ts',
    'prettier.config.cts',
    'prettier.config.mts',
)
PRETTIER_EXTENSIONS = {
    '.cjs', '.css', '.graphql', '.html', '.js', '.json', '.json5', '.jsx',
    '.less', '.md', '.mdx', '.mjs', '.mts', '.scss', '.ts', '.tsx', '.vue',
    '.yaml', '.yml',
}
OXLINT_EXTENSIONS = {'.cjs', '.js', '.jsx', '.mjs', '.mts', '.ts', '.tsx', '.vue'}


@dataclass(frozen=True)
class FormatterCommand:
    """A formatter command and the repository directory it should run from."""

    args: List[str]
    cwd: Path
    timeout: int = 10


def resolve_file_path(file_path: str, project_dir: Optional[str] = None) -> Path:
    """Resolve hook paths against the project directory used by the harness."""
    path = Path(file_path).expanduser()
    if path.is_absolute():
        return path.resolve()

    base = Path(project_dir or os.getcwd()).expanduser()
    return (base / path).resolve()


def find_repository_root(file_path: Path, project_dir: Optional[str] = None) -> Optional[Path]:
    """Find the nearest Git root, falling back to the harness project directory."""
    for directory in file_path.parents:
        if (directory / '.git').exists():
            return directory

    if project_dir:
        project_path = Path(project_dir).expanduser().resolve()
        if file_path == project_path or project_path in file_path.parents:
            return project_path

    return None


def _ancestors_to_root(file_path: Path, repository_root: Path) -> List[Path]:
    directories = []
    current = file_path.parent
    while current == repository_root or repository_root in current.parents:
        directories.append(current)
        if current == repository_root:
            break
        current = current.parent
    return directories


def _package_uses_prettier(package_json: Path) -> bool:
    try:
        with package_json.open(encoding='utf-8') as package_file:
            package = json.load(package_file)
        return isinstance(package, dict) and 'prettier' in package
    except (OSError, ValueError):
        return False


def find_prettier_config(file_path: Path, repository_root: Path) -> Optional[Path]:
    """Find the nearest Prettier config that applies to the edited file."""
    for directory in _ancestors_to_root(file_path, repository_root):
        for config_name in PRETTIER_CONFIG_FILES:
            config_path = directory / config_name
            if config_path.is_file():
                return config_path

        package_json = directory / 'package.json'
        if package_json.is_file() and _package_uses_prettier(package_json):
            return package_json

    return None


def find_oxlint_config(file_path: Path, repository_root: Path) -> Optional[Path]:
    """Find the nearest Oxlint config that applies to the edited file."""
    for directory in _ancestors_to_root(file_path, repository_root):
        config_path = directory / '.oxlintrc.json'
        if config_path.is_file():
            return config_path
    return None


def find_executable(name: str, start: Path, repository_root: Path) -> Optional[str]:
    """Prefer a repository-local binary before falling back to the current PATH."""
    current = start
    while current == repository_root or repository_root in current.parents:
        executable = current / 'node_modules' / '.bin' / name
        if executable.is_file() and os.access(executable, os.X_OK):
            return str(executable)
        if current == repository_root:
            break
        current = current.parent
    return shutil.which(name)


def detect_formatter(file_path: Path, repository_root: Path) -> Optional[FormatterCommand]:
    """Choose Prettier, then Oxlint, or no formatter for an edited file."""
    extension = file_path.suffix.lower()
    prettier_config = find_prettier_config(file_path, repository_root)
    if prettier_config:
        if extension not in PRETTIER_EXTENSIONS:
            return None
        prettier = find_executable('prettier', prettier_config.parent, repository_root)
        if prettier:
            return FormatterCommand(
                [prettier, '--write', str(file_path)],
                repository_root,
            )
        return None

    oxlint_config = find_oxlint_config(file_path, repository_root)
    if oxlint_config and extension in OXLINT_EXTENSIONS:
        oxlint = find_executable('oxlint', oxlint_config.parent, repository_root)
        if oxlint:
            return FormatterCommand(
                [oxlint, '--fix', '--config', str(oxlint_config), str(file_path)],
                repository_root,
            )

    return None
