#!/usr/bin/env python3
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name('refresh-gh-token.py')
SPEC = importlib.util.spec_from_file_location('refresh_gh_token', MODULE_PATH)
refresh_gh_token = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(refresh_gh_token)


class RefreshGhTokenTest(unittest.TestCase):
    def test_token_is_fresh_until_maximum_age(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Path(temp_dir) / 'settings.json'
            settings.write_text(json.dumps({'env': {'GH_TOKEN': 'token'}}))
            os.utime(settings, (100, 100))

            self.assertTrue(refresh_gh_token.token_is_fresh(settings, now=200))
            self.assertFalse(
                refresh_gh_token.token_is_fresh(
                    settings,
                    now=100 + refresh_gh_token.MAX_TOKEN_AGE_SECONDS,
                )
            )

    def test_token_is_fresh_rejects_unusable_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Path(temp_dir) / 'settings.json'
            self.assertFalse(refresh_gh_token.token_is_fresh(settings))

            settings.write_text('{invalid')
            self.assertFalse(refresh_gh_token.token_is_fresh(settings))

            settings.write_text(json.dumps({'env': {'GH_TOKEN': '  '}}))
            self.assertFalse(refresh_gh_token.token_is_fresh(settings))


if __name__ == '__main__':
    unittest.main()
