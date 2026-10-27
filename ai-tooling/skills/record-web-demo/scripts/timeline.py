from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

EventKind = Literal["focus", "wide", "caption", "url", "idle", "voice"]


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Event:
    t: float
    kind: EventKind
    box: Box | None = None
    text: str | None = None
    end: float | None = None


@dataclass
class Timeline:
    origin: float = field(default_factory=time.time)
    events: list[Event] = field(default_factory=list)

    def reset(self) -> None:
        self.origin = time.time()
        self.events.clear()

    def now(self) -> float:
        return time.time() - self.origin

    def focus(self, box: Box) -> None:
        self.events.append(Event(self.now(), "focus", box=box))

    def wide(self) -> None:
        self.events.append(Event(self.now(), "wide"))

    def caption(self, text: str | None) -> None:
        self.events.append(Event(self.now(), "caption", text=text))

    def url(self, url: str) -> None:
        self.events.append(Event(self.now(), "url", text=url))

    def voice(self, path: Path, duration: float) -> None:
        start = self.now()
        self.events.append(Event(start, "voice", text=str(path), end=start + duration))

    def idle(self, start: float) -> None:
        self.events.append(Event(start, "idle", end=self.now()))

    def write(self, path: Path) -> None:
        path.write_text(json.dumps([asdict(event) for event in self.events], indent=1), encoding="utf-8")
