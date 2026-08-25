#!/usr/bin/env python3
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name('gh_wrapper.py')
SPEC = importlib.util.spec_from_file_location('gh_wrapper', MODULE_PATH)
gh_wrapper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gh_wrapper)


class GhWrapperTest(unittest.TestCase):
    def test_load_token_reads_local_overlay(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Path(temp_dir) / 'settings.json'
            settings.write_text(json.dumps({'env': {'GH_TOKEN': ' current-token '}}))

            self.assertEqual(gh_wrapper.load_token(settings), 'current-token')

    def test_load_token_rejects_missing_or_invalid_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Path(temp_dir) / 'settings.json'
            self.assertIsNone(gh_wrapper.load_token(settings))
            settings.write_text('{invalid')
            self.assertIsNone(gh_wrapper.load_token(settings))

    def test_stale_token_uses_file_age(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Path(temp_dir) / 'settings.json'
            settings.write_text('{}')
            os.utime(settings, (100, 100))

            self.assertFalse(gh_wrapper.token_is_stale(settings, now=200))
            self.assertTrue(gh_wrapper.token_is_stale(settings, now=100 + 45 * 60))

    def test_find_real_gh_skips_the_wrapper_symlink(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrapper_target = root / 'gh_wrapper.py'
            wrapper_target.write_text('')
            wrapper_target.chmod(0o755)
            shim_dir = root / 'shim'
            real_dir = root / 'real'
            shim_dir.mkdir()
            real_dir.mkdir()
            (shim_dir / 'gh').symlink_to(wrapper_target)
            real_gh = real_dir / 'gh'
            real_gh.write_text('')
            real_gh.chmod(0o755)

            found = gh_wrapper.find_real_gh(
                os.pathsep.join([str(shim_dir), str(real_dir)]), wrapper_target
            )

            self.assertEqual(found, real_gh)

    def test_bot_environment_replaces_stale_tokens_without_mutating_input(self):
        original = {
            'GH_TOKEN': 'expired',
            'GITHUB_TOKEN': 'also-expired',
            'AI_GIT_ALLOWED_OWNERS': 'nicholasgriffintn',
        }

        child = gh_wrapper.bot_environment(original, 'fresh')

        self.assertEqual(child['GH_TOKEN'], 'fresh')
        self.assertNotIn('GITHUB_TOKEN', child)
        self.assertEqual(original['GH_TOKEN'], 'expired')

    @mock.patch.object(gh_wrapper.subprocess, 'run')
    def test_refresh_does_not_contaminate_gh_stdout(self, run):
        gh_wrapper.refresh_token()

        run.assert_called_once_with(
            [gh_wrapper.sys.executable, str(gh_wrapper.REFRESH_SCRIPT)],
            check=True,
            stdout=gh_wrapper.subprocess.DEVNULL,
        )


if __name__ == '__main__':
    unittest.main()
