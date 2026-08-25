#!/usr/bin/env python3
import multiprocessing
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.token_lock import gh_token_refresh_lock


def hold_lock(lock_path, acquired, release):
    with gh_token_refresh_lock(lock_path):
        acquired.set()
        release.wait(5)


class TokenLockTest(unittest.TestCase):
    def test_lock_serialises_refreshes_and_uses_private_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / 'cache' / 'refresh.lock'
            context = multiprocessing.get_context('fork')
            child_acquired = context.Event()
            release_child = context.Event()
            child = context.Process(
                target=hold_lock,
                args=(lock_path, child_acquired, release_child),
            )
            child.start()
            self.assertTrue(child_acquired.wait(2))

            parent_acquired = threading.Event()

            def acquire_in_parent():
                with gh_token_refresh_lock(lock_path):
                    parent_acquired.set()

            waiter = threading.Thread(target=acquire_in_parent)
            waiter.start()
            self.assertFalse(parent_acquired.wait(0.1))
            release_child.set()
            self.assertTrue(parent_acquired.wait(2))
            waiter.join(2)
            child.join(2)

            self.assertEqual(child.exitcode, 0)
            self.assertFalse(waiter.is_alive())
            self.assertEqual(stat.S_IMODE(lock_path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(lock_path.stat().st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
