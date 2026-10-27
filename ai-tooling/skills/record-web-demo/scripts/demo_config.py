from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from audio_providers import TTS_PROVIDERS

TARGET_KEYS = ("selector", "role", "text", "label", "placeholder", "testId")
WAIT_UNTIL = ("load", "domcontentloaded", "networkidle", "commit")
COLOR_SCHEMES = ("light", "dark", "no-preference")
STEP_FIELDS: dict[str, tuple[set[str], set[str]]] = {
    "goto": ({"url"}, set()),
    "caption": ({"text"}, set()),
    "wait": ({"ms"}, set()),
    "scroll": (set(), {"target", "to"}),
    "hover": ({"target"}, set()),
    "click": ({"target"}, {"waitForResponse"}),
    "type": ({"target", "text"}, {"replace", "delay", "waitForResponse"}),
    "select": ({"target"}, {"value", "label"}),
    "press": ({"key"}, {"target", "waitForResponse"}),
    "waitFor": (set(), {"target", "response", "timeout"}),
}
COMMON_STEP_FIELDS = {"do", "caption", "pause", "zoom", "say"}
HEX_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_FRAME = {"background": ["#6366f1", "#ec4899"], "chrome": True, "padding": 0.045}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class DemoConfig:
    url: str
    output: Path
    steps: list[dict[str, Any]]
    viewport: tuple[int, int] = (1440, 900)
    speed: float = 1.0
    wait_until: str = "load"
    color_scheme: str = "light"
    gif: dict[str, int] | None = None
    restore_files: list[Path] = field(default_factory=list)
    setup: list[dict[str, Any]] = field(default_factory=list)
    resolution: int = 2
    fps: int = 30
    zoom_max: float | None = 1.8
    frame: dict[str, Any] | None = None
    trim_waits: bool = True
    hide: list[str] = field(default_factory=list)
    css: str = ""
    storage_state: Path | None = None
    narration: dict[str, Any] | None = None
    music: dict[str, Any] | None = None


def _require_http_url(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.startswith(("http://", "https://")):
        errors.append(f"{where}: must be an http(s) URL")


def _check_secret_text(value: Any, where: str, errors: list[str]) -> None:
    if isinstance(value, str):
        return
    if isinstance(value, dict) and set(value) == {"env"} and isinstance(value["env"], str):
        return
    errors.append(f'{where}: must be a string or {{"env": "VAR_NAME"}}')


def _check_target(value: Any, where: str, errors: list[str]) -> None:
    if isinstance(value, str) and value:
        return
    if not isinstance(value, dict):
        errors.append(f"{where}: must be a CSS selector string or a target object")
        return
    kinds = [key for key in TARGET_KEYS if key in value]
    if len(kinds) != 1:
        errors.append(f"{where}: needs exactly one of {', '.join(TARGET_KEYS)}")
    unknown = set(value) - set(TARGET_KEYS) - {"name", "nth", "exact"}
    if unknown:
        errors.append(f"{where}: unknown keys {sorted(unknown)}")
    if "name" in value and "role" not in value:
        errors.append(f"{where}: 'name' only applies to role targets")
    if "nth" in value and not (isinstance(value["nth"], int) and value["nth"] >= 0):
        errors.append(f"{where}: 'nth' must be a non-negative integer")


def _check_step(step: Any, where: str, errors: list[str]) -> None:
    if not isinstance(step, dict):
        errors.append(f"{where}: must be an object")
        return
    verb = step.get("do")
    if verb not in STEP_FIELDS:
        errors.append(f"{where}: 'do' must be one of {', '.join(STEP_FIELDS)}")
        return
    required, optional = STEP_FIELDS[verb]
    missing = required - set(step)
    if missing:
        errors.append(f"{where} ({verb}): missing {sorted(missing)}")
    unknown = set(step) - required - optional - COMMON_STEP_FIELDS
    if unknown:
        errors.append(f"{where} ({verb}): unknown keys {sorted(unknown)}")
    if "target" in step:
        _check_target(step["target"], f"{where}.target", errors)
    if verb == "goto" and "url" in step:
        _require_http_url(step["url"], f"{where}.url", errors)
    if verb == "type" and "text" in step:
        _check_secret_text(step["text"], f"{where}.text", errors)
    if verb == "scroll" and ("target" in step) == ("to" in step):
        errors.append(f"{where} (scroll): needs exactly one of 'target' or 'to'")
    if verb == "scroll" and "to" in step and step["to"] not in ("top", "bottom"):
        errors.append(f"{where} (scroll): 'to' must be 'top' or 'bottom'")
    if verb == "select" and ("value" in step) == ("label" in step):
        errors.append(f"{where} (select): needs exactly one of 'value' or 'label'")
    if verb == "waitFor" and ("target" in step) == ("response" in step):
        errors.append(f"{where} (waitFor): needs exactly one of 'target' or 'response'")
    for key in ("ms", "pause", "delay", "timeout"):
        if key in step and not (isinstance(step[key], (int, float)) and step[key] >= 0):
            errors.append(f"{where}.{key}: must be a non-negative number of milliseconds")
    if "caption" in step and step["caption"] is not None and not isinstance(step["caption"], str):
        errors.append(f"{where}.caption: must be a string or null")
    if "zoom" in step and not isinstance(step["zoom"], bool):
        errors.append(f"{where}.zoom: must be true or false")
    if "say" in step and not (isinstance(step["say"], str) and step["say"].strip()):
        errors.append(f"{where}.say: must be non-empty narration text")


def _parse_narration(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    allowed = {"provider", "voice", "style", "model", "fromCaptions"}
    if not isinstance(value, dict) or set(value) - allowed:
        errors.append(f"narration: must be an object with keys {sorted(allowed)}")
        return None
    if value.get("provider") not in TTS_PROVIDERS:
        errors.append(f"narration.provider: must be one of {', '.join(TTS_PROVIDERS)}")
    if not (isinstance(value.get("voice"), str) and value["voice"]):
        errors.append("narration.voice: required; list options with the `voices` command")
    for key in ("style", "model"):
        if key in value and not isinstance(value[key], str):
            errors.append(f"narration.{key}: must be a string")
    if "fromCaptions" in value and not isinstance(value["fromCaptions"], bool):
        errors.append("narration.fromCaptions: must be true or false")
    return {"fromCaptions": False, **value}


def _parse_music(value: Any, config_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    if value is None:
        return None
    sources = ("file", "jamendo", "generate")
    if not isinstance(value, dict) or set(value) - {*sources, "volume"}:
        errors.append('music: must be {"file" | "jamendo" | "generate": ..., "volume": 0-1}')
        return None
    chosen = [key for key in sources if key in value]
    if len(chosen) != 1:
        errors.append("music: needs exactly one of file, jamendo or generate")
        return None
    source = chosen[0]
    if not (isinstance(value[source], str) and value[source].strip()):
        errors.append(f"music.{source}: must be a non-empty string")
        return None
    volume = value.get("volume", 0.22)
    if not (isinstance(volume, (int, float)) and 0 < volume <= 1):
        errors.append("music.volume: must be between 0 and 1")
    music = {"source": source, "value": value[source], "volume": float(volume)}
    if source == "file":
        path = (config_dir / value["file"]).resolve()
        if not path.is_file():
            errors.append(f"music.file: {path} does not exist")
        music["value"] = path
    return music


def _check_steps(value: Any, name: str, errors: list[str], required: bool) -> list[dict[str, Any]]:
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        errors.append(f"{name}: must be a {'non-empty ' if required else ''}array")
        return []
    for index, step in enumerate(value):
        _check_step(step, f"{name}[{index}]", errors)
    return value


def _parse_zoom(value: Any, errors: list[str]) -> float | None:
    if value is False:
        return None
    if value is True or value is None:
        return 1.8
    if isinstance(value, dict) and set(value) <= {"max"}:
        zoom_max = value.get("max", 1.8)
        if isinstance(zoom_max, (int, float)) and 1.2 <= zoom_max <= 3:
            return float(zoom_max)
    errors.append('zoom: must be true, false or {"max": 1.2-3}')
    return None


def _parse_frame(value: Any, errors: list[str]) -> dict[str, Any] | None:
    if value is None or value is False:
        return None
    if value is True:
        return dict(DEFAULT_FRAME)
    if not isinstance(value, dict) or set(value) - set(DEFAULT_FRAME):
        errors.append('frame: must be true, false or {"background", "chrome", "padding"}')
        return None
    frame = {**DEFAULT_FRAME, **value}
    background = frame["background"]
    colours = background if isinstance(background, list) else [background]
    if not (1 <= len(colours) <= 2 and all(isinstance(c, str) and HEX_COLOUR.match(c) for c in colours)):
        errors.append('frame.background: must be "#rrggbb" or ["#rrggbb", "#rrggbb"]')
    if not isinstance(frame["chrome"], bool):
        errors.append("frame.chrome: must be true or false")
    if not (isinstance(frame["padding"], (int, float)) and 0 <= frame["padding"] <= 0.2):
        errors.append("frame.padding: must be a fraction of the width between 0 and 0.2")
    frame["background"] = colours
    return frame


def _resolve_inside(base: Path, value: str, root: Path, where: str, errors: list[str]) -> Path | None:
    path = (base / value).resolve()
    if not path.is_relative_to(root):
        errors.append(f"{where}: {path} is outside the working directory {root}")
        return None
    if path.is_dir():
        errors.append(f"{where}: {path} is a directory; list files individually")
        return None
    return path


def parse_config(raw: Any, config_dir: Path, root: Path) -> DemoConfig:
    errors: list[str] = []
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")

    known = {
        "url", "output", "steps", "setup", "viewport", "speed", "waitUntil", "colorScheme", "gif", "restoreFiles",
        "resolution", "fps", "zoom", "frame", "trimWaits", "hide", "css", "storageState", "narration", "music",
    }
    unknown = set(raw) - known
    if unknown:
        errors.append(f"unknown top-level keys {sorted(unknown)}")

    _require_http_url(raw.get("url"), "url", errors)

    output = raw.get("output")
    if not isinstance(output, str) or not output.lower().endswith(".mp4"):
        errors.append("output: must be a path ending in .mp4")

    steps = _check_steps(raw.get("steps"), "steps", errors, required=True)
    setup = _check_steps(raw.get("setup"), "setup", errors, required=False)

    resolution = raw.get("resolution", 2)
    if resolution not in (1, 2):
        errors.append("resolution: must be 1 or 2")
    fps = raw.get("fps", 30)
    if fps not in (24, 30, 60):
        errors.append("fps: must be 24, 30 or 60")
    zoom_max = _parse_zoom(raw.get("zoom"), errors)
    frame = _parse_frame(raw.get("frame"), errors)
    trim_waits = raw.get("trimWaits", True)
    if not isinstance(trim_waits, bool):
        errors.append("trimWaits: must be true or false")
    hide = raw.get("hide", [])
    if not (isinstance(hide, list) and all(isinstance(item, str) and item for item in hide)):
        errors.append("hide: must be an array of CSS selectors")
        hide = []
    css = raw.get("css", "")
    if not isinstance(css, str):
        errors.append("css: must be a string")
        css = ""
    narration = _parse_narration(raw.get("narration"), errors)
    music = _parse_music(raw.get("music"), config_dir, errors)
    if narration is None and any("say" in step for step in steps if isinstance(step, dict)):
        errors.append("steps use 'say' but no narration provider is configured")
    storage_state = None
    if "storageState" in raw:
        if isinstance(raw["storageState"], str) and (config_dir / raw["storageState"]).is_file():
            storage_state = (config_dir / raw["storageState"]).resolve()
        else:
            errors.append("storageState: must be the path of an existing Playwright storage state file")

    viewport = raw.get("viewport", {"width": 1440, "height": 900})
    if not (
        isinstance(viewport, dict)
        and all(isinstance(viewport.get(k), int) and 320 <= viewport[k] <= 3840 for k in ("width", "height"))
    ):
        errors.append("viewport: needs integer width and height between 320 and 3840")
        viewport = {"width": 1440, "height": 900}

    speed = raw.get("speed", 1.0)
    if not (isinstance(speed, (int, float)) and 0.25 <= speed <= 4):
        errors.append("speed: must be a number between 0.25 and 4")

    wait_until = raw.get("waitUntil", "load")
    if wait_until not in WAIT_UNTIL:
        errors.append(f"waitUntil: must be one of {', '.join(WAIT_UNTIL)}")

    color_scheme = raw.get("colorScheme", "light")
    if color_scheme not in COLOR_SCHEMES:
        errors.append(f"colorScheme: must be one of {', '.join(COLOR_SCHEMES)}")

    gif = raw.get("gif")
    if gif is True:
        gif = {}
    if gif is False:
        gif = None
    if gif is not None:
        if not isinstance(gif, dict) or set(gif) - {"width", "fps"}:
            errors.append('gif: must be true, false or {"width": int, "fps": int}')
            gif = None
        else:
            gif = {"width": gif.get("width", 960), "fps": gif.get("fps", 12)}
            if not all(isinstance(v, int) and v > 0 for v in gif.values()):
                errors.append("gif: width and fps must be positive integers")

    restore_files: list[Path] = []
    restore_raw = raw.get("restoreFiles", [])
    if not isinstance(restore_raw, list) or not all(isinstance(p, str) for p in restore_raw):
        errors.append("restoreFiles: must be an array of paths")
        restore_raw = []
    for index, entry in enumerate(restore_raw):
        path = _resolve_inside(config_dir, entry, root, f"restoreFiles[{index}]", errors)
        if path:
            restore_files.append(path)

    if errors:
        raise ConfigError("invalid demo config:\n  - " + "\n  - ".join(errors))

    return DemoConfig(
        url=raw["url"],
        output=(config_dir / output).resolve(),
        steps=steps,
        viewport=(viewport["width"], viewport["height"]),
        speed=float(speed),
        wait_until=wait_until,
        color_scheme=color_scheme,
        gif=gif,
        restore_files=restore_files,
        setup=setup,
        resolution=resolution,
        fps=fps,
        zoom_max=zoom_max,
        frame=frame,
        trim_waits=trim_waits,
        hide=hide,
        css=css,
        storage_state=storage_state,
        narration=narration,
        music=music,
    )


def load_config(path: Path, root: Path) -> DemoConfig:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"config not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path}: invalid JSON at line {error.lineno}: {error.msg}") from error
    return parse_config(raw, path.resolve().parent, root.resolve())


def resolve_text(value: str | dict[str, str]) -> str:
    if isinstance(value, str):
        return value
    name = value["env"]
    if name not in os.environ:
        raise ConfigError(f"environment variable {name} is not set")
    return os.environ[name]
