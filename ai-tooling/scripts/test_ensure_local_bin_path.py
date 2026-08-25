#!/usr/bin/env python3
import importlib.util
import stat
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name('ensure-local-bin-path.py')
SPEC = importlib.util.spec_from_file_location('ensure_local_bin_path', MODULE_PATH)
ensure_path = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ensure_path)


class EnsureLocalBinPathTest(unittest.TestCase):
    def test_appends_path_block_and_preserves_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / '.zshrc'
            zshrc.write_text('export EXAMPLE=1\n')
            zshrc.chmod(0o644)

            changed = ensure_path.ensure_local_bin_path(zshrc)

            self.assertTrue(changed)
            self.assertTrue(zshrc.read_text().endswith(ensure_path.PATH_BLOCK + '\n'))
            self.assertEqual(stat.S_IMODE(zshrc.stat().st_mode), 0o644)

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / '.zshrc'
            zshrc.write_text(ensure_path.PATH_BLOCK + '\n')

            self.assertFalse(ensure_path.ensure_local_bin_path(zshrc))
            self.assertEqual(zshrc.read_text().count(ensure_path.START_MARKER), 1)

    def test_missing_zshrc_is_not_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zshrc = Path(temp_dir) / '.zshrc'

            self.assertFalse(ensure_path.ensure_local_bin_path(zshrc))
            self.assertFalse(zshrc.exists())

    def test_fresh_install_template_contains_managed_block(self):
        template = MODULE_PATH.parents[2] / 'zshrc-template'

        self.assertEqual(template.read_text().count(ensure_path.PATH_BLOCK), 1)


if __name__ == '__main__':
    unittest.main()
