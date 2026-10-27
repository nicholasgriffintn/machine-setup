from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from audio_providers import download_jamendo, generate_music, synthesise
from demo_config import DemoConfig
from media import media_duration


@dataclass(frozen=True)
class Clip:
    path: Path
    duration: float


def cache_dir(config: DemoConfig) -> Path:
    return config.output.parent / ".audio-cache"


def cache_key(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, default=str).encode()).hexdigest()[:20]


def narration_lines(steps: list[dict[str, Any]], from_captions: bool) -> dict[int, str]:
    lines: dict[int, str] = {}
    for index, step in enumerate(steps):
        text = step.get("say")
        if text is None and from_captions:
            text = step.get("text") if step["do"] == "caption" else step.get("caption")
        if isinstance(text, str) and text.strip():
            lines[index] = text.strip()
    return lines


def prepare_narration(config: DemoConfig) -> dict[int, Clip]:
    settings = config.narration
    if not settings:
        return {}
    clips: dict[int, Clip] = {}
    for index, text in narration_lines(config.steps, settings["fromCaptions"]).items():
        identity = (settings["provider"], settings["voice"], settings.get("style"), settings.get("model"), text)
        path = cache_dir(config) / f"voice-{cache_key(*identity)}.wav"
        if not path.is_file():
            synthesise(settings["provider"], settings["voice"], text, path, settings.get("style"), settings.get("model"))
        clips[index] = Clip(path, media_duration(path))
    return clips


def prepare_music(config: DemoConfig, duration: float) -> tuple[Path | None, str | None]:
    music = config.music
    if not music:
        return None, None
    if music["source"] == "file":
        return music["value"], None
    if music["source"] == "jamendo":
        path = cache_dir(config) / f"jamendo-{cache_key(music['value'])}.mp3"
        credit = download_jamendo(music["value"], path)
        return path, credit
    path = cache_dir(config) / f"generated-{cache_key(music['value'], round(duration))}.mp3"
    if not path.is_file():
        generate_music(music["value"], duration, path)
    return path, "Music generated with ElevenLabs Music"
