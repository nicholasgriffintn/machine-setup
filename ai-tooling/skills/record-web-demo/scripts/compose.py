from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, BinaryIO

from PIL import Image, ImageDraw, ImageFilter

from camera import CameraPath, TimeMap
from imaging import diagonal_gradient, hex_to_rgb, load_font, rounded_mask
from screencast import Frame
from timeline import Event

CAPTION_FADE_SECONDS = 0.25


@dataclass(frozen=True)
class Layout:
    canvas: tuple[int, int]
    content: tuple[int, int, int, int]
    chrome_height: int
    radius: int


def plan_layout(viewport: tuple[int, int], resolution: int, frame: dict[str, Any] | None) -> Layout:
    width, height = viewport[0] * resolution, viewport[1] * resolution
    if not frame:
        return Layout((width, height), (0, 0, width, height), 0, 0)
    padding = round(width * frame["padding"])
    chrome = round(width * 0.026) if frame["chrome"] else 0
    content_w = width - padding * 2
    content_h = round(content_w * viewport[1] / viewport[0])
    if content_h + chrome + padding * 2 > height:
        content_h = height - chrome - padding * 2
        content_w = round(content_h * viewport[0] / viewport[1])
    left = (width - content_w) // 2
    top = (height - content_h - chrome) // 2 + chrome
    return Layout((width, height), (left, top, content_w, content_h), chrome, round(width * 0.008))


class Compositor:
    def __init__(
        self,
        frames: list[Frame],
        origin: float,
        events: list[Event],
        camera: CameraPath,
        time_map: TimeMap,
        viewport: tuple[int, int],
        layout: Layout,
        frame_style: dict[str, Any] | None,
    ):
        self.frames = frames
        self.frame_times = [frame.timestamp - origin for frame in frames]
        self.camera = camera
        self.time_map = time_map
        self.viewport = viewport
        self.layout = layout
        self.frame_style = frame_style
        self.captions = [(event.t, event.text) for event in events if event.kind == "caption"]
        self.caption_times = [t for t, _ in self.captions]
        self.urls = [(event.t, event.text or "") for event in events if event.kind == "url"]
        self.url_times = [t for t, _ in self.urls]
        self._decoded: tuple[int, Image.Image] | None = None
        self._last_key: tuple[Any, ...] | None = None
        self._last_bytes = b""
        self.background = self._render_background() if frame_style else None

    def _source(self, t: float) -> tuple[int, Image.Image]:
        index = max(0, bisect_right(self.frame_times, t) - 1)
        if self._decoded is None or self._decoded[0] != index:
            with Image.open(self.frames[index].path) as image:
                self._decoded = (index, image.convert("RGB"))
        return self._decoded

    def _caption_state(self, t: float) -> tuple[str | None, float]:
        index = bisect_right(self.caption_times, t) - 1
        if index < 0:
            return None, 0.0
        since, text = self.captions[index]
        if text:
            return text, min(1.0, (t - since) / CAPTION_FADE_SECONDS)
        previous = self.captions[index - 1][1] if index > 0 else None
        fading = 1 - (t - since) / CAPTION_FADE_SECONDS
        return (previous, fading) if previous and fading > 0 else (None, 0.0)

    def _url(self, t: float) -> str:
        index = bisect_right(self.url_times, t) - 1
        return self.urls[index][1] if index >= 0 else ""

    def _render_background(self) -> Image.Image:
        assert self.frame_style is not None
        width, height = self.layout.canvas
        colours = [hex_to_rgb(c) for c in self.frame_style["background"]]
        background = diagonal_gradient((width, height), colours[0], colours[-1])
        left, top, content_w, content_h = self.layout.content
        window = (left, top - self.layout.chrome_height, left + content_w, top + content_h)
        shadow = Image.new("L", (width, height), 0)
        offset = round(width * 0.006)
        ImageDraw.Draw(shadow).rounded_rectangle(
            (window[0], window[1] + offset, window[2], window[3] + offset), self.layout.radius, fill=110
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(round(width * 0.012)))
        background.paste((0, 0, 0), (0, 0, width, height), shadow)
        return background

    @lru_cache(maxsize=32)
    def _chrome_bar(self, url: str) -> Image.Image:
        left, _, content_w, _ = self.layout.content
        height = self.layout.chrome_height
        bar = Image.new("RGB", (content_w, height), (241, 243, 245))
        draw = ImageDraw.Draw(bar)
        dot = round(height * 0.26)
        for index, colour in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
            cx = round(height * 0.55) + index * round(dot * 1.7)
            draw.ellipse((cx - dot // 2, height // 2 - dot // 2, cx + dot // 2, height // 2 + dot // 2), fill=colour)
        pill_w = round(content_w * 0.42)
        pill_h = round(height * 0.62)
        pill = ((content_w - pill_w) // 2, (height - pill_h) // 2, (content_w + pill_w) // 2, (height + pill_h) // 2)
        draw.rounded_rectangle(pill, pill_h // 2, fill=(255, 255, 255))
        font = load_font(round(height * 0.36))
        label = url.removeprefix("https://").removeprefix("http://").rstrip("/")
        while label and draw.textlength(label, font=font) > pill_w - pill_h:
            label = label[:-2] + "…" if len(label) > 2 else ""
        draw.text((content_w // 2, height // 2), label, font=font, fill=(75, 85, 99), anchor="mm")
        return bar

    @lru_cache(maxsize=64)
    def _caption_image(self, text: str) -> Image.Image:
        _, _, content_w, _ = self.layout.content
        size = max(14, round(content_w * 0.0165))
        font = load_font(size)
        probe = ImageDraw.Draw(Image.new("L", (1, 1)))
        max_width = round(content_w * 0.7)
        words, lines, line = text.split(), [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and probe.textlength(candidate, font=font) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
        line_height = round(size * 1.35)
        text_w = max(round(probe.textlength(item, font=font)) for item in lines)
        pad_x, pad_y = round(size * 0.95), round(size * 0.6)
        image = Image.new("RGBA", (text_w + pad_x * 2, line_height * len(lines) + pad_y * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, image.width - 1, image.height - 1), round(size * 0.7), fill=(17, 24, 39, 228))
        for index, item in enumerate(lines):
            draw.text((image.width // 2, pad_y + line_height * index + line_height // 2), item, font=font, fill=(249, 250, 251, 255), anchor="mm")
        return image

    def render(self, output_t: float) -> bytes:
        t = self.time_map.source_time(output_t)
        index, source = self._source(t)
        view = self.camera.at(t)
        caption, alpha = self._caption_state(t)
        url = self._url(t) if self.layout.chrome_height else ""
        key = (index, round(view.cx, 1), round(view.cy, 1), round(view.scale, 4), caption, round(alpha, 2), url)
        if key == self._last_key:
            return self._last_bytes

        left, top, content_w, content_h = self.layout.content
        ratio = source.width / self.viewport[0]
        half_w = self.viewport[0] / view.scale / 2
        half_h = self.viewport[1] / view.scale / 2
        box = ((view.cx - half_w) * ratio, (view.cy - half_h) * ratio, (view.cx + half_w) * ratio, (view.cy + half_h) * ratio)
        content = source.resize((content_w, content_h), Image.Resampling.BICUBIC, box=box)

        if caption and alpha > 0:
            pill = self._caption_image(caption)
            if alpha < 1:
                pill = pill.copy()
                pill.putalpha(pill.getchannel("A").point(lambda value: round(value * alpha)))
            position = ((content_w - pill.width) // 2, content_h - pill.height - round(content_h * 0.05))
            content.paste(pill, position, pill)

        if self.background is None:
            canvas = content
        else:
            canvas = self.background.copy()
            radius = self.layout.radius
            window_top = top - self.layout.chrome_height
            mask = rounded_mask(content_w, content_h + self.layout.chrome_height, radius)
            window = Image.new("RGB", mask.size)
            if self.layout.chrome_height:
                window.paste(self._chrome_bar(url), (0, 0))
            window.paste(content, (0, self.layout.chrome_height))
            canvas.paste(window, (left, window_top), mask)

        self._last_key = key
        self._last_bytes = canvas.tobytes()
        return self._last_bytes

    def write(self, sink: BinaryIO, fps: int) -> int:
        total = max(1, round(self.time_map.duration * fps))
        for frame_index in range(total):
            sink.write(self.render(frame_index / fps))
        return total

