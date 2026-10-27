from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

from http_client import HttpError, request, request_json
from media import to_wav

TTS_PROVIDERS = ("say", "openai", "elevenlabs")
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
OPENAI_VOICES = (
    "alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar",
)
ELEVENLABS_TTS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_API = "https://api.elevenlabs.io"
JAMENDO_TRACKS = "https://api.jamendo.com/v3.0/tracks/"
ALLOWED_LICENCES = ("/by/", "/by-sa/")
SAY_VOICE_LINE = re.compile(r"^(?P<name>.+?)\s+(?P<locale>[a-z]{2,3}_[A-Z0-9]{2,3})\s+#\s*(?P<sample>.*)$")


class AudioError(RuntimeError):
    pass


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise AudioError(f"{name} is not set; export it in the shell that runs the recorder")
    return value


def list_voices(provider: str, locale: str | None = None) -> list[dict[str, Any]]:
    if provider == "say":
        if shutil.which("say") is None:
            raise AudioError("the 'say' provider needs macOS")
        listing = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=True).stdout
        voices = []
        for line in listing.splitlines():
            match = SAY_VOICE_LINE.match(line.strip())
            if match and (locale is None or match["locale"].startswith(locale)):
                voices.append({"id": match["name"], "locale": match["locale"]})
        return voices
    if provider == "openai":
        return [{"id": voice} for voice in OPENAI_VOICES]
    if provider == "elevenlabs":
        data = _call(lambda: request_json(
            f"{ELEVENLABS_API}/v2/voices?page_size=100",
            headers={"xi-api-key": require_env("ELEVENLABS_API_KEY")},
        ))
        return [
            {
                "id": voice["voice_id"],
                "name": voice.get("name"),
                "labels": voice.get("labels", {}),
                "previewUrl": voice.get("preview_url"),
            }
            for voice in data.get("voices", [])
        ]
    raise AudioError(f"unknown narration provider {provider!r}")


def _call(action: Any) -> Any:
    try:
        return action()
    except HttpError as error:
        raise AudioError(str(error)) from error


def synthesise(provider: str, voice: str, text: str, output: Path, style: str | None = None, model: str | None = None) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="record-web-demo-tts-") as workdir:
        raw = Path(workdir) / "speech"
        if provider == "say":
            if shutil.which("say") is None:
                raise AudioError("the 'say' provider needs macOS")
            raw = raw.with_suffix(".aiff")
            subprocess.run(["say", "-v", voice, "-o", str(raw), "--", text], check=True, capture_output=True)
        elif provider == "openai":
            body: dict[str, Any] = {"model": model or OPENAI_TTS_MODEL, "input": text, "voice": voice, "response_format": "wav"}
            if style:
                body["instructions"] = style
            raw = raw.with_suffix(".wav")
            raw.write_bytes(_call(lambda: request(
                "https://api.openai.com/v1/audio/speech",
                method="POST",
                headers={"Authorization": f"Bearer {require_env('OPENAI_API_KEY')}"},
                body=body,
            )))
        elif provider == "elevenlabs":
            raw = raw.with_suffix(".mp3")
            voice_path = urllib.parse.quote(voice, safe="")
            raw.write_bytes(_call(lambda: request(
                f"{ELEVENLABS_API}/v1/text-to-speech/{voice_path}?output_format=mp3_44100_128",
                method="POST",
                headers={"xi-api-key": require_env("ELEVENLABS_API_KEY")},
                body={"text": text, "model_id": model or ELEVENLABS_TTS_MODEL},
            )))
        else:
            raise AudioError(f"unknown narration provider {provider!r}")
        to_wav(raw, output)
    return output


def _track_summary(track: dict[str, Any]) -> dict[str, Any]:
    licence = track.get("license_ccurl", "")
    return {
        "id": str(track["id"]),
        "title": track.get("name"),
        "artist": track.get("artist_name"),
        "durationSeconds": track.get("duration"),
        "licence": licence,
        "page": track.get("shareurl"),
        "preview": track.get("audio"),
        "credit": f"\"{track.get('name')}\" by {track.get('artist_name')} ({licence}) via Jamendo",
    }


def _usable(track: dict[str, Any]) -> bool:
    licence = track.get("license_ccurl", "")
    return bool(track.get("audiodownload_allowed") and track.get("audiodownload")) and any(
        marker in licence for marker in ALLOWED_LICENCES
    )


def search_music(query: str, limit: int = 8, vocals: bool = False) -> list[dict[str, Any]]:
    params = {
        "client_id": require_env("JAMENDO_CLIENT_ID"),
        "format": "json",
        "limit": str(min(max(limit * 3, 10), 50)),
        "search": query,
        "include": "licenses musicinfo",
        "audioformat": "mp32",
        "boost": "popularity_total",
    }
    if not vocals:
        params["vocalinstrumental"] = "instrumental"
    data = _call(lambda: request_json(f"{JAMENDO_TRACKS}?{urllib.parse.urlencode(params)}"))
    return [_track_summary(track) for track in data.get("results", []) if _usable(track)][:limit]


def download_jamendo(track_id: str, output: Path) -> str:
    params = {"client_id": require_env("JAMENDO_CLIENT_ID"), "format": "json", "id": track_id, "audioformat": "mp32"}
    results = _call(lambda: request_json(f"{JAMENDO_TRACKS}?{urllib.parse.urlencode(params)}")).get("results", [])
    if not results:
        raise AudioError(f"Jamendo track {track_id} not found")
    track = results[0]
    if not _usable(track):
        raise AudioError(f"Jamendo track {track_id} is not downloadable under an attribution-only or share-alike licence")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_call(lambda: request(track["audiodownload"])))
    return _track_summary(track)["credit"]


def generate_music(prompt: str, seconds: float, output: Path) -> None:
    length_ms = min(max(round(seconds * 1000), 3000), 600_000)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_call(lambda: request(
        f"{ELEVENLABS_API}/v1/music?output_format=mp3_44100_128",
        method="POST",
        headers={"xi-api-key": require_env("ELEVENLABS_API_KEY")},
        body={"prompt": prompt, "music_length_ms": length_ms, "force_instrumental": True},
        timeout=600,
    )))
