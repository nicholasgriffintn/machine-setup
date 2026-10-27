from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Browser, Playwright, sync_playwright

from audio_providers import TTS_PROVIDERS, AudioError, list_voices, search_music, synthesise
from camera import CameraPath, Shot, TimeMap, plan_shots, wide_view
from compose import Compositor, plan_layout
from demo_config import ConfigError, DemoConfig, load_config
from demo_steps import StepError, StepRunner
from file_snapshot import restored_afterwards
from media import MediaError, contact_sheet, make_gif, media_duration, mix_audio, probe, raw_encoder, require_ffmpeg
from narration import Clip, prepare_music, prepare_narration
from screencast import Frame, Screencast
from timeline import Timeline

SCRIPTS_DIR = Path(__file__).resolve().parent
OVERLAY_JS = SCRIPTS_DIR / "overlay.js"
INSTALL_HINT = f"uv run --project {SCRIPTS_DIR} playwright install chromium"


class RecordingFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class Capture:
    frames: list[Frame]
    timeline: Timeline
    duration: float


def launch_browser(playwright: Playwright, headed: bool) -> Browser:
    try:
        return playwright.chromium.launch(headless=not headed)
    except Exception as bundled_error:
        if "Executable doesn't exist" not in str(bundled_error):
            raise
    try:
        return playwright.chromium.launch(headless=not headed, channel="chrome")
    except Exception as error:
        raise RecordingFailed(f"no usable Chromium: run `{INSTALL_HINT}` or install Google Chrome") from error


def page_style_script(config: DemoConfig) -> str | None:
    rules = "".join(f"{selector}{{visibility:hidden !important}}" for selector in config.hide) + config.css
    if not rules:
        return None
    return (
        "(css => { const apply = () => { const s = document.createElement('style'); s.textContent = css;"
        " document.documentElement.append(s); };"
        " document.documentElement ? apply() : document.addEventListener('DOMContentLoaded', apply); })"
        f"({json.dumps(rules)});"
    )


def capture(config: DemoConfig, workdir: Path, headed: bool, clips: dict[int, Clip]) -> Capture:
    failure_shot = config.output.with_suffix(".failure.png")
    failure_shot.unlink(missing_ok=True)
    width, height = config.viewport
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headed)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=config.resolution,
            color_scheme=config.color_scheme,
            storage_state=str(config.storage_state) if config.storage_state else None,
        )
        context.add_init_script(path=str(OVERLAY_JS))
        style_script = page_style_script(config)
        if style_script:
            context.add_init_script(script=style_script)
        page = context.new_page()
        timeline = Timeline()
        page.on("framenavigated", lambda frame: timeline.url(frame.url) if frame == page.main_frame else None)
        screencast = Screencast(context, page, workdir, (width * config.resolution, height * config.resolution))
        try:
            try:
                page.goto(config.url, wait_until=config.wait_until, timeout=30_000)
            except Exception as error:
                raise RecordingFailed(f"could not load {config.url}; is the server running? ({error})") from error
            runner = StepRunner(page, config, timeline)
            for index, step in enumerate(config.setup):
                runner.run(f"setup {index}", step)
            timeline.reset()
            timeline.url(page.url)
            screencast.start()
            runner.start()
            for index, step in enumerate(config.steps):
                runner.run(f"step {index}", step, clips.get(index))
            runner.finish()
            duration = timeline.now()
        except (StepError, RecordingFailed) as error:
            failure_shot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(failure_shot))
            raise RecordingFailed(f"{error}\nscreenshot of the failing state: {failure_shot}") from error
        finally:
            screencast.stop()
            context.close()
            browser.close()
    if not screencast.frames:
        raise RecordingFailed("the screencast produced no frames")
    return Capture(screencast.frames, timeline, duration)


def render(config: DemoConfig, captured: Capture) -> TimeMap:
    timeline = captured.timeline
    if config.zoom_max:
        shots = plan_shots(timeline.events, config.viewport, config.zoom_max)
    else:
        shots = [Shot(0.0, wide_view(config.viewport))]
    idle = [(e.t, e.end) for e in timeline.events if e.kind == "idle" and e.end is not None] if config.trim_waits else []
    voices = [(e.t, e.end) for e in timeline.events if e.kind == "voice" and e.end is not None]
    time_map = TimeMap(captured.duration, idle, protected=voices)
    layout = plan_layout(config.viewport, config.resolution, config.frame)
    compositor = Compositor(
        captured.frames,
        timeline.origin,
        timeline.events,
        CameraPath(shots),
        time_map,
        config.viewport,
        layout,
        config.frame,
    )
    with raw_encoder(config.output, layout.canvas, config.fps) as sink:
        compositor.write(sink, config.fps)
    timeline.write(config.output.with_suffix(".timeline.json"))
    return time_map


def add_audio(config: DemoConfig, captured: Capture, time_map: TimeMap) -> str | None:
    voices = [
        (time_map.output_time(event.t), Path(event.text))
        for event in captured.timeline.events
        if event.kind == "voice" and event.text
    ]
    music, credit = prepare_music(config, time_map.duration)
    if music is None and not voices:
        return None
    mix_audio(config.output, voices, music, config.music["volume"] if config.music else 0.0, time_map.duration)
    return credit


def record(config_path: Path, headed: bool) -> dict[str, object]:
    require_ffmpeg()
    config = load_config(config_path, Path.cwd())
    clips = prepare_narration(config)
    with restored_afterwards(config.restore_files) as restore_problems:
        with tempfile.TemporaryDirectory(prefix="record-web-demo-") as workdir:
            captured = capture(config, Path(workdir), headed, clips)
            time_map = render(config, captured)
    credit = add_audio(config, captured, time_map)

    summary = probe(config.output)
    sheet = config.output.with_suffix(".contact.png")
    frame_times = contact_sheet(config.output, sheet, float(summary["durationSeconds"]))
    summary["contactSheet"] = str(sheet)
    summary["contactSheetFrameSeconds"] = frame_times
    summary["timeline"] = str(config.output.with_suffix(".timeline.json"))
    summary["narrationLines"] = len(clips)
    if credit:
        summary["musicCredit"] = credit
    if config.gif:
        gif_path = config.output.with_suffix(".gif")
        make_gif(config.output, gif_path, config.gif["width"], config.gif["fps"])
        summary["gif"] = str(gif_path)
    if config.restore_files:
        summary["restoredFiles"] = [str(path) for path in config.restore_files]
    if restore_problems:
        summary["restoreProblems"] = restore_problems
    return summary


def inspect(url: str, viewport: tuple[int, int], scope: str, screenshot: Path | None, color_scheme: str) -> str:
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headed=False)
        try:
            page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]}, color_scheme=color_scheme)
            page.goto(url, wait_until="load", timeout=30_000)
            if screenshot:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot), full_page=True)
            return page.locator(scope).first.aria_snapshot()
        finally:
            browser.close()


def parse_viewport(value: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x"))
    except ValueError as error:
        raise argparse.ArgumentTypeError("viewport must look like 1440x900") from error
    return width, height


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="record_demo", description="Record polished website demo videos.")
    commands = parser.add_subparsers(dest="command", required=True)

    record_cmd = commands.add_parser("record", help="run a demo config and write the MP4")
    record_cmd.add_argument("config", type=Path)
    record_cmd.add_argument("--headed", action="store_true", help="show the browser while recording")

    validate_cmd = commands.add_parser("validate", help="check a demo config without opening a browser")
    validate_cmd.add_argument("config", type=Path)

    inspect_cmd = commands.add_parser("inspect", help="print the accessibility tree to pick targets")
    inspect_cmd.add_argument("url")
    inspect_cmd.add_argument("--scope", default="body", help="CSS selector to limit the tree")
    inspect_cmd.add_argument("--viewport", type=parse_viewport, default=(1440, 900))
    inspect_cmd.add_argument("--color-scheme", choices=("light", "dark"), default="light")
    inspect_cmd.add_argument("--screenshot", type=Path, help="also save a full-page screenshot")

    voices_cmd = commands.add_parser("voices", help="list narration voices for a provider")
    voices_cmd.add_argument("--provider", choices=TTS_PROVIDERS, required=True)
    voices_cmd.add_argument("--locale", help="filter say voices by locale prefix, such as en_GB")

    preview_cmd = commands.add_parser("preview-voice", help="synthesise a sample line so the user can pick a voice")
    preview_cmd.add_argument("--provider", choices=TTS_PROVIDERS, required=True)
    preview_cmd.add_argument("--voice", required=True)
    preview_cmd.add_argument("--text", required=True)
    preview_cmd.add_argument("--style", help="delivery instructions (OpenAI only)")
    preview_cmd.add_argument("--out", type=Path, required=True)

    music_cmd = commands.add_parser("music-search", help="find attribution-licensed tracks on Jamendo")
    music_cmd.add_argument("query")
    music_cmd.add_argument("--limit", type=int, default=6)
    music_cmd.add_argument("--vocals", action="store_true", help="allow tracks with vocals")

    args = parser.parse_args(argv)
    try:
        if args.command == "voices":
            print(json.dumps(list_voices(args.provider, args.locale), indent=2))
        elif args.command == "preview-voice":
            path = synthesise(args.provider, args.voice, args.text, args.out.with_suffix(".wav"), args.style)
            print(json.dumps({"path": str(path), "durationSeconds": round(media_duration(path), 2)}, indent=2))
        elif args.command == "music-search":
            print(json.dumps(search_music(args.query, args.limit, args.vocals), indent=2))
        elif args.command == "validate":
            config = load_config(args.config, Path.cwd())
            print(json.dumps({"ok": True, "steps": len(config.steps), "output": str(config.output)}, indent=2))
        elif args.command == "inspect":
            print(inspect(args.url, args.viewport, args.scope, args.screenshot, args.color_scheme))
        else:
            print(json.dumps(record(args.config, args.headed), indent=2))
    except (AudioError, ConfigError, MediaError, RecordingFailed) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
