from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page


@dataclass(frozen=True)
class Frame:
    timestamp: float
    path: Path


class Screencast:
    def __init__(self, context: BrowserContext, page: Page, directory: Path, size: tuple[int, int]):
        self.directory = directory
        self.size = size
        self.frames: list[Frame] = []
        self.running = False
        self.session = context.new_cdp_session(page)
        self.session.on("Page.screencastFrame", self._on_frame)

    def _on_frame(self, event: dict[str, Any]) -> None:
        self.session.send("Page.screencastFrameAck", {"sessionId": event["sessionId"]})
        if not self.running:
            return
        path = self.directory / f"{len(self.frames):06d}.jpg"
        path.write_bytes(base64.b64decode(event["data"]))
        self.frames.append(Frame(event["metadata"]["timestamp"], path))

    def start(self) -> None:
        self.running = True
        width, height = self.size
        self.session.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": 92, "maxWidth": width, "maxHeight": height, "everyNthFrame": 1},
        )

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        try:
            self.session.send("Page.stopScreencast")
        except Exception:
            pass
