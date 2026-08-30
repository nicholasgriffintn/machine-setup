#!/usr/bin/env python3
"""Tests for repository-aware format-on-edit detection."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

LIB_DIR = Path(__file__).parent.parent / 'lib'
HOOK_SCRIPT = Path(__file__).parent / 'format-on-edit.py'
sys.path.insert(0, str(LIB_DIR))

from formatter_detection import detect_formatter, find_repository_root, resolve_file_path


class FormatterDetectionTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name).resolve()
        (self.repo / '.git').mkdir()
        self.source_dir = self.repo / 'src'
        self.source_dir.mkdir()
        self.source_file = self.source_dir / 'app.ts'
        self.source_file.write_text('const value=1\n', encoding='utf-8')

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_binary(self, name):
        binary_dir = self.repo / 'node_modules' / '.bin'
        binary_dir.mkdir(parents=True, exist_ok=True)
        binary = binary_dir / name
        binary.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return binary

    def test_prettier_config_and_local_binary_take_priority(self):
        prettier_config = self.repo / '.prettierrc.json'
        prettier_config.write_text('{}\n', encoding='utf-8')
        (self.repo / '.oxlintrc.json').write_text('{}\n', encoding='utf-8')
        prettier = self.add_binary('prettier')
        self.add_binary('oxlint')

        formatter = detect_formatter(self.source_file, self.repo)

        self.assertIsNotNone(formatter)
        self.assertEqual(
            formatter.args,
            [
                str(prettier),
                '--write',
                str(self.source_file),
            ],
        )
        self.assertEqual(formatter.cwd, self.repo)

    def test_package_json_prettier_field_counts_as_config(self):
        package_json = self.repo / 'package.json'
        package_json.write_text(json.dumps({'prettier': {}}), encoding='utf-8')
        prettier = self.add_binary('prettier')

        formatter = detect_formatter(self.source_file, self.repo)

        self.assertIsNotNone(formatter)
        self.assertEqual(formatter.args[0], str(prettier))
        self.assertEqual(formatter.args[1], '--write')

    def test_oxlint_is_used_when_prettier_is_not_configured(self):
        oxlint_config = self.repo / '.oxlintrc.json'
        oxlint_config.write_text('{}\n', encoding='utf-8')
        oxlint = self.add_binary('oxlint')

        formatter = detect_formatter(self.source_file, self.repo)

        self.assertIsNotNone(formatter)
        self.assertEqual(
            formatter.args,
            [
                str(oxlint),
                '--fix',
                '--config',
                str(oxlint_config),
                str(self.source_file),
            ],
        )

    def test_no_config_means_no_formatter(self):
        self.add_binary('prettier')
        self.add_binary('oxlint')

        self.assertIsNone(detect_formatter(self.source_file, self.repo))

    def test_missing_prettier_binary_does_not_fall_back_to_oxlint(self):
        (self.repo / '.prettierrc.json').write_text('{}\n', encoding='utf-8')
        (self.repo / '.oxlintrc.json').write_text('{}\n', encoding='utf-8')
        self.add_binary('oxlint')

        with mock.patch('formatter_detection.shutil.which', return_value=None):
            self.assertIsNone(detect_formatter(self.source_file, self.repo))

    def test_oxlint_does_not_run_for_unsupported_files(self):
        (self.repo / '.oxlintrc.json').write_text('{}\n', encoding='utf-8')
        self.add_binary('oxlint')
        markdown_file = self.source_dir / 'README.md'
        markdown_file.write_text('# Title\n', encoding='utf-8')

        self.assertIsNone(detect_formatter(markdown_file, self.repo))

    def test_relative_paths_resolve_against_project_directory(self):
        resolved = resolve_file_path('src/app.ts', str(self.repo))

        self.assertEqual(resolved, self.source_file)
        self.assertEqual(find_repository_root(resolved), self.repo)

    def test_hook_runs_detected_formatter_with_repository_as_cwd(self):
        (self.repo / '.prettierrc.json').write_text('{}\n', encoding='utf-8')
        formatter_args = self.repo / 'formatter-args.txt'
        prettier = self.add_binary('prettier')
        prettier.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$PWD" "$@" > "$FORMATTER_ARGS_FILE"\n',
            encoding='utf-8',
        )
        environment = os.environ.copy()
        environment['CLAUDE_PROJECT_DIR'] = str(self.repo)
        environment['FORMATTER_ARGS_FILE'] = str(formatter_args)

        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps({'tool_input': {'file_path': 'src/app.ts'}}),
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            formatter_args.read_text(encoding='utf-8').splitlines(),
            [str(self.repo), '--write', str(self.source_file)],
        )


if __name__ == '__main__':
    unittest.main()
