from __future__ import annotations

import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class MediaError(RuntimeError):
    pass


def require_ffmpeg() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise MediaError(f"{' and '.join(missing)} not found on PATH; install with `brew install ffmpeg`")


def _run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-8:])
        raise MediaError(f"{args[0]} failed ({result.returncode}):\n{tail}")
    return result.stdout


@contextmanager
def raw_encoder(output: Path, size: tuple[int, int], fps: int) -> Iterator[BinaryIO]:
    output.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(output),
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stderr is not None
    try:
        yield process.stdin
    finally:
        try:
            process.stdin.close()
        except BrokenPipeError:
            pass
        stderr = process.stderr.read().decode(errors="replace")
        if process.wait() != 0:
            raise MediaError(f"ffmpeg encode failed:\n{stderr.strip()[-800:]}")


def make_gif(video: Path, output: Path, width: int, fps: int) -> None:
    scale = f"fps={fps},scale={width}:-1:flags=lanczos"
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
        "-filter_complex", f"{scale},split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
        str(output),
    ])


def probe(video: Path) -> dict[str, object]:
    data = json.loads(_run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,pix_fmt:format=duration,size",
        "-of", "json", str(video),
    ]))
    stream = data["streams"][0]
    return {
        "path": str(video),
        "codec": stream["codec_name"],
        "width": stream["width"],
        "height": stream["height"],
        "pixFmt": stream["pix_fmt"],
        "durationSeconds": round(float(data["format"]["duration"]), 2),
        "sizeBytes": int(data["format"]["size"]),
    }


def contact_sheet(video: Path, output: Path, duration: float, frames: int = 12, columns: int = 4) -> list[float]:
    rows = -(-frames // columns)
    rate = frames / max(duration, 0.1)
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
        "-vf", f"fps={rate:.4f},scale=480:-2,tile={columns}x{rows}:padding=4:color=white",
        "-frames:v", "1", "-update", "1", str(output),
    ])
    return [round((index + 0.5) / rate, 1) for index in range(frames)]


def media_duration(path: Path) -> float:
    output = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(output.strip())


def to_wav(source: Path, output: Path) -> None:
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-ar", "48000", "-ac", "2", str(output)])


def mix_audio(
    video: Path,
    voices: list[tuple[float, Path]],
    music: Path | None,
    music_volume: float,
    duration: float,
) -> None:
    if not voices and music is None:
        return
    inputs = ["-i", str(video)]
    filters: list[str] = []
    voice_labels: list[str] = []
    for index, (start, clip) in enumerate(voices, start=1):
        inputs += ["-i", str(clip)]
        delay = max(0, round(start * 1000))
        filters.append(f"[{index}:a]aresample=48000,adelay=delays={delay}:all=1[v{index}]")
        voice_labels.append(f"[v{index}]")
    if voice_labels:
        filters.append(f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:normalize=0:duration=longest[voice]")
    if music is not None:
        music_index = len(voices) + 1
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        fade_out = max(0.0, duration - 2.5)
        filters.append(
            f"[{music_index}:a]aresample=48000,atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=1.2,afade=t=out:st={fade_out:.3f}:d=2.5,volume={music_volume}[music]"
        )
    if voice_labels and music is not None:
        filters.append("[voice]asplit[voice_key][voice_mix]")
        filters.append("[music][voice_key]sidechaincompress=threshold=0.02:ratio=12:attack=20:release=450[ducked]")
        filters.append("[ducked][voice_mix]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[aout]")
    elif voice_labels:
        filters.append("[voice]apad,alimiter=limit=0.95[aout]")
    else:
        filters.append("[music]anull[aout]")

    mixed = video.with_suffix(".mixing.mp4")
    try:
        _run([
            "ffmpeg", "-y", "-loglevel", "error", *inputs,
            "-filter_complex", ";".join(filters),
            "-map", "0:v", "-map", "[aout]", "-t", f"{duration:.3f}",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            str(mixed),
        ])
        mixed.replace(video)
    finally:
        mixed.unlink(missing_ok=True)
