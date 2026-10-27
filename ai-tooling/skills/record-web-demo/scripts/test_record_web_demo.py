#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camera import CameraPath, TimeMap, plan_shots
from demo_config import ConfigError, parse_config, resolve_text
from file_snapshot import restored_afterwards
from narration import narration_lines
from timeline import Box, Event

VIEWPORT = (1440, 900)
SMALL_BUTTON = Box(1000, 20, 60, 24)


def valid_raw(**overrides):
    raw = {
        "url": "http://localhost:3000",
        "output": "demo.mp4",
        "steps": [{"do": "click", "target": {"role": "button", "name": "Save"}}],
    }
    raw.update(overrides)
    return raw


class ParseConfigTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.config_dir = self.root / ".demo-recording"
        self.config_dir.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def parse(self, raw):
        return parse_config(raw, self.config_dir, self.root)

    def test_resolves_paths_against_the_config_directory(self):
        config = self.parse(valid_raw(restoreFiles=["../data/db.json"]))
        self.assertEqual(config.output, self.config_dir / "demo.mp4")
        self.assertEqual(config.restore_files, [self.root / "data" / "db.json"])

    def test_reports_every_problem_with_its_step_index(self):
        raw = valid_raw(
            output="demo.mov",
            steps=[
                {"do": "click"},
                {"do": "type", "target": {"role": "textbox", "text": "x"}, "text": "a"},
                {"do": "teleport"},
            ],
        )
        with self.assertRaises(ConfigError) as caught:
            self.parse(raw)
        message = str(caught.exception)
        self.assertIn("output: must be a path ending in .mp4", message)
        self.assertIn("steps[0] (click): missing ['target']", message)
        self.assertIn("steps[1].target: needs exactly one of", message)
        self.assertIn("steps[2]: 'do' must be one of", message)

    def test_rejects_restore_paths_outside_the_working_directory(self):
        with self.assertRaises(ConfigError) as caught:
            self.parse(valid_raw(restoreFiles=["../../etc/hosts"]))
        self.assertIn("outside the working directory", str(caught.exception))

    def test_rejects_bad_presentation_options(self):
        with self.assertRaises(ConfigError) as caught:
            self.parse(valid_raw(zoom={"max": 9}, frame={"background": "pink"}, resolution=3))
        message = str(caught.exception)
        self.assertIn("zoom:", message)
        self.assertIn("frame.background:", message)
        self.assertIn("resolution:", message)

    def test_rejects_narration_and_music_mistakes(self):
        steps = [{"do": "click", "target": "a", "say": "Hello"}]
        with self.assertRaises(ConfigError) as caught:
            self.parse(valid_raw(steps=steps, music={"file": "missing.mp3", "generate": "lofi"}))
        message = str(caught.exception)
        self.assertIn("music: needs exactly one of", message)
        self.assertIn("no narration provider is configured", message)

    def test_rejects_non_http_urls(self):
        with self.assertRaises(ConfigError):
            self.parse(valid_raw(url="file:///etc/passwd"))

    def test_secret_text_reads_from_environment(self):
        os.environ["RECORD_WEB_DEMO_TEST_SECRET"] = "s3cret"
        self.addCleanup(os.environ.pop, "RECORD_WEB_DEMO_TEST_SECRET")
        self.assertEqual(resolve_text({"env": "RECORD_WEB_DEMO_TEST_SECRET"}), "s3cret")
        with self.assertRaises(ConfigError):
            resolve_text({"env": "RECORD_WEB_DEMO_MISSING"})


class RestoreFilesTest(unittest.TestCase):
    def test_restores_changed_files_and_removes_created_ones_even_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            existing = Path(temp) / "db.bin"
            existing.write_bytes(b"\x00\xffbefore")
            created = Path(temp) / "new.json"
            with self.assertRaises(RuntimeError):
                with restored_afterwards([existing, created]):
                    existing.write_bytes(b"after")
                    created.write_text("{}")
                    raise RuntimeError("step failed")
            self.assertEqual(existing.read_bytes(), b"\x00\xffbefore")
            self.assertFalse(created.exists())

    def test_leaves_directories_created_at_a_restore_path_and_reports_them(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "uploads"
            with restored_afterwards([path]) as problems:
                path.mkdir()
                (path / "keep.txt").write_text("x")
            self.assertTrue((path / "keep.txt").exists())
            self.assertEqual(len(problems), 1)


class CameraPlanTest(unittest.TestCase):
    def test_zooms_onto_small_targets_and_back_out_after_a_lull(self):
        events = [Event(1.0, "focus", box=SMALL_BUTTON), Event(3.0, "wide"), Event(6.0, "focus", box=SMALL_BUTTON)]
        shots = plan_shots(events, VIEWPORT, max_zoom=1.8)
        self.assertEqual([round(shot.view.scale, 2) for shot in shots], [1.0, 1.8, 1.0, 1.8])
        camera = CameraPath(shots)
        self.assertEqual(camera.at(0.5).scale, 1.0)
        self.assertAlmostEqual(camera.at(2.5).scale, 1.8)
        self.assertLess(camera.at(1.2).scale, 1.8)

    def test_pans_between_close_steps_instead_of_zooming_out(self):
        events = [Event(1.0, "focus", box=SMALL_BUTTON), Event(2.0, "wide"), Event(2.5, "focus", box=Box(100, 600, 60, 24))]
        shots = plan_shots(events, VIEWPORT, max_zoom=1.8)
        self.assertEqual([round(shot.view.scale, 2) for shot in shots], [1.0, 1.8, 1.8])

    def test_navigation_resets_to_a_wide_shot(self):
        events = [
            Event(0.0, "url", text="https://a.test/"),
            Event(1.0, "focus", box=SMALL_BUTTON),
            Event(1.5, "url", text="https://a.test/blog"),
        ]
        shots = plan_shots(events, VIEWPORT, max_zoom=1.8)
        self.assertEqual((shots[-1].start, shots[-1].view.scale), (1.5, 1.0))

    def test_large_targets_stay_wide(self):
        events = [Event(1.0, "focus", box=Box(0, 0, 1400, 800))]
        self.assertEqual(len(plan_shots(events, VIEWPORT, max_zoom=1.8)), 1)


class TimeMapTest(unittest.TestCase):
    def test_long_waits_are_compressed_and_short_ones_kept(self):
        time_map = TimeMap(duration=10.0, idle=[(2.0, 6.0), (7.0, 7.3)], keep=0.5)
        self.assertAlmostEqual(time_map.duration, 6.5)
        self.assertAlmostEqual(time_map.source_time(1.0), 1.0)
        self.assertAlmostEqual(time_map.source_time(2.5), 6.0)
        self.assertAlmostEqual(time_map.source_time(6.5), 10.0)
        self.assertAlmostEqual(time_map.output_time(8.0), 4.5)

    def test_waits_under_narration_play_at_full_speed(self):
        time_map = TimeMap(duration=10.0, idle=[(2.0, 6.0)], keep=0.5, protected=[(1.5, 3.0)])
        self.assertAlmostEqual(time_map.duration, 10.0)


class NarrationTest(unittest.TestCase):
    def test_explicit_lines_win_and_captions_are_read_only_when_asked(self):
        steps = [
            {"do": "caption", "text": "Welcome"},
            {"do": "click", "target": "a", "caption": "Opening the blog", "say": "Here is the blog"},
            {"do": "click", "target": "b", "caption": None},
        ]
        self.assertEqual(narration_lines(steps, from_captions=False), {1: "Here is the blog"})
        self.assertEqual(narration_lines(steps, from_captions=True), {0: "Welcome", 1: "Here is the blog"})


if __name__ == "__main__":
    unittest.main()
