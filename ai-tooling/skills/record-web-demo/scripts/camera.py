from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass

from timeline import Box, Event

TRANSITION_SECONDS = 0.8
MERGE_GAP_SECONDS = 1.2
FOCUS_PADDING = 140
MIN_USEFUL_ZOOM = 1.15
IDLE_KEEP_SECONDS = 0.5


@dataclass(frozen=True)
class View:
    cx: float
    cy: float
    scale: float


@dataclass(frozen=True)
class Shot:
    start: float
    view: View


def ease_in_out(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def wide_view(viewport: tuple[int, int]) -> View:
    return View(viewport[0] / 2, viewport[1] / 2, 1.0)


def clamp_view(view: View, viewport: tuple[int, int]) -> View:
    width, height = viewport
    half_w = width / view.scale / 2
    half_h = height / view.scale / 2
    return View(
        min(max(view.cx, half_w), width - half_w),
        min(max(view.cy, half_h), height - half_h),
        view.scale,
    )


def focus_view(box: Box, viewport: tuple[int, int], max_zoom: float) -> View:
    width, height = viewport
    needed_width = max(box.width + FOCUS_PADDING * 2, (box.height + FOCUS_PADDING * 2) * width / height)
    scale = min(max(width / needed_width, 1.0), max_zoom)
    if scale < MIN_USEFUL_ZOOM:
        return wide_view(viewport)
    return clamp_view(View(box.x + box.width / 2, box.y + box.height / 2, scale), viewport)


def contains(outer: View, box: Box, viewport: tuple[int, int]) -> bool:
    half_w = viewport[0] / outer.scale / 2
    half_h = viewport[1] / outer.scale / 2
    margin = 24
    return (
        box.x - margin >= outer.cx - half_w
        and box.x + box.width + margin <= outer.cx + half_w
        and box.y - margin >= outer.cy - half_h
        and box.y + box.height + margin <= outer.cy + half_h
    )


def navigations(events: list[Event]) -> list[Event]:
    result: list[Event] = []
    previous: str | None = None
    for event in sorted((event for event in events if event.kind == "url"), key=lambda event: event.t):
        if previous is not None and event.text != previous:
            result.append(Event(event.t, "wide"))
        previous = event.text
    return result


def plan_shots(events: list[Event], viewport: tuple[int, int], max_zoom: float) -> list[Shot]:
    cues = [event for event in events if event.kind in ("focus", "wide")] + navigations(events)
    moves = sorted(cues, key=lambda event: event.t)
    shots = [Shot(0.0, wide_view(viewport))]
    for index, event in enumerate(moves):
        if event.kind == "wide":
            following = moves[index + 1] if index + 1 < len(moves) else None
            if following and following.kind == "focus" and following.t - event.t < MERGE_GAP_SECONDS:
                continue
            view = wide_view(viewport)
        else:
            assert event.box is not None
            current = shots[-1].view
            if current.scale > 1 and contains(current, event.box, viewport):
                continue
            view = focus_view(event.box, viewport, max_zoom)
        if view != shots[-1].view:
            shots.append(Shot(event.t, view))
    return shots


def _blend(a: View, b: View, progress: float) -> View:
    eased = ease_in_out(min(max(progress, 0.0), 1.0))
    scale = math.exp(math.log(a.scale) + (math.log(b.scale) - math.log(a.scale)) * eased)
    return View(a.cx + (b.cx - a.cx) * eased, a.cy + (b.cy - a.cy) * eased, scale)


class CameraPath:
    def __init__(self, shots: list[Shot], transition: float = TRANSITION_SECONDS):
        self.shots = shots
        self.transition = transition
        self.starts = [shot.start for shot in shots]
        self.origins = [shots[0].view]
        for index in range(1, len(shots)):
            self.origins.append(self._at_index(index - 1, shots[index].start))

    def _at_index(self, index: int, t: float) -> View:
        shot = self.shots[index]
        if index == 0:
            return shot.view
        return _blend(self.origins[index], shot.view, (t - shot.start) / self.transition)

    def at(self, t: float) -> View:
        index = max(0, bisect_right(self.starts, t) - 1)
        return self._at_index(index, t)


def overlaps(span: tuple[float, float], others: list[tuple[float, float]]) -> bool:
    return any(span[0] < other_end and other_start < span[1] for other_start, other_end in others)


class TimeMap:
    def __init__(
        self,
        duration: float,
        idle: list[tuple[float, float]],
        keep: float = IDLE_KEEP_SECONDS,
        protected: list[tuple[float, float]] | None = None,
    ):
        self.segments: list[tuple[float, float, float]] = []
        source = 0.0
        output = 0.0
        for start, end in sorted(idle):
            if start < source or end - start <= keep + 0.2 or end > duration or overlaps((start, end), protected or []):
                continue
            self.segments.append((output, source, 1.0))
            output += start - source
            self.segments.append((output, start, (end - start) / keep))
            output += keep
            source = end
        self.segments.append((output, source, 1.0))
        self.duration = output + (duration - source)
        self.output_starts = [segment[0] for segment in self.segments]
        self.source_starts = [segment[1] for segment in self.segments]

    def source_time(self, output_t: float) -> float:
        index = max(0, bisect_right(self.output_starts, output_t) - 1)
        out_start, src_start, rate = self.segments[index]
        return src_start + (output_t - out_start) * rate

    def output_time(self, source_t: float) -> float:
        index = max(0, bisect_right(self.source_starts, source_t) - 1)
        out_start, src_start, rate = self.segments[index]
        return out_start + (source_t - src_start) / rate
