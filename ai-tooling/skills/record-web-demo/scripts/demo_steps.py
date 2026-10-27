from __future__ import annotations

import math
from contextlib import contextmanager
from typing import Any, Iterator

from playwright.sync_api import Locator, Page

from demo_config import DemoConfig, resolve_text
from narration import Clip
from timeline import Box, Timeline

TARGET_TIMEOUT_MS = 10_000
RESPONSE_TIMEOUT_MS = 15_000
NARRATION_GAP_SECONDS = 0.35
DEFAULT_PAUSE_MS = {
    "goto": 900,
    "caption": 1600,
    "wait": 0,
    "scroll": 500,
    "hover": 800,
    "click": 800,
    "type": 700,
    "select": 800,
    "press": 600,
    "waitFor": 300,
}


class StepError(RuntimeError):
    def __init__(self, label: str, step: dict[str, Any], cause: Exception):
        self.step = step
        first_line = str(cause).strip().splitlines()[0] if str(cause).strip() else type(cause).__name__
        super().__init__(f"{label} ({describe(step)}) failed: {first_line}")


def describe_target(target: str | dict[str, Any]) -> str:
    if isinstance(target, str):
        return f"selector {target!r}"
    kind = next(key for key in ("selector", "role", "text", "label", "placeholder", "testId") if key in target)
    text = f"{kind} {target[kind]!r}"
    if "name" in target:
        text += f" name={target['name']!r}"
    if "nth" in target:
        text += f" nth={target['nth']}"
    return text


def describe(step: dict[str, Any]) -> str:
    verb = step["do"]
    if "target" in step:
        return f"{verb} {describe_target(step['target'])}"
    detail = step.get("url") or step.get("key") or step.get("to") or step.get("response") or step.get("ms")
    return f"{verb} {detail}" if detail is not None else verb


class StepRunner:
    def __init__(self, page: Page, config: DemoConfig, timeline: Timeline):
        self.page = page
        self.config = config
        self.timeline = timeline
        self.zoom_step = True
        width, height = config.viewport
        self.mouse = (width * 0.62, height * 0.58)

    def ms(self, value: float) -> float:
        return value / self.config.speed

    def hold(self, value: float) -> None:
        if value > 0:
            self.page.wait_for_timeout(self.ms(value))

    def start(self) -> None:
        self.page.mouse.move(*self.mouse)
        self.hold(900)

    def finish(self) -> None:
        self._clear_highlight()
        self.hold(1400)

    def run(self, label: str, step: dict[str, Any], clip: Clip | None = None) -> None:
        try:
            started = self.timeline.now()
            if clip:
                self.timeline.voice(clip.path, clip.duration)
            self.zoom_step = step.get("zoom", True)
            if "caption" in step:
                self._caption(step["caption"])
            getattr(self, f"_do_{step['do']}")(step)
            self.hold(step.get("pause", DEFAULT_PAUSE_MS[step["do"]]))
            if clip:
                remaining = clip.duration + NARRATION_GAP_SECONDS - (self.timeline.now() - started)
                if remaining > 0:
                    self.page.wait_for_timeout(remaining * 1000)
            self._clear_highlight()
            if "target" in step:
                self.timeline.wide()
        except Exception as error:
            raise StepError(label, step, error) from error

    def locate(self, target: str | dict[str, Any], timeout: float = TARGET_TIMEOUT_MS) -> Locator:
        if isinstance(target, str):
            target = {"selector": target}
        exact = target.get("exact")
        page = self.page
        if "selector" in target:
            locator = page.locator(target["selector"])
        elif "role" in target:
            locator = page.get_by_role(target["role"], name=target.get("name"), exact=exact)
        elif "text" in target:
            locator = page.get_by_text(target["text"], exact=exact)
        elif "label" in target:
            locator = page.get_by_label(target["label"], exact=exact)
        elif "placeholder" in target:
            locator = page.get_by_placeholder(target["placeholder"], exact=exact)
        else:
            locator = page.get_by_test_id(target["testId"])

        waiting_from = self.timeline.now()
        if "nth" in target:
            locator = locator.nth(target["nth"])
            locator.wait_for(state="visible", timeout=timeout)
            self.timeline.idle(waiting_from)
            return locator
        locator.first.wait_for(state="visible", timeout=timeout)
        self.timeline.idle(waiting_from)
        count = locator.count()
        if count > 1:
            raise ValueError(f"{describe_target(target)} matches {count} elements; add 'nth' or narrow the target")
        return locator

    def _caption(self, text: str | None) -> None:
        self.timeline.caption(text)

    def _clear_highlight(self) -> None:
        self.page.evaluate("() => window.__demo && window.__demo.clearHighlight()")

    def _glide_to(self, x: float, y: float) -> None:
        start_x, start_y = self.mouse
        dx, dy = x - start_x, y - start_y
        distance = math.hypot(dx, dy)
        steps = max(12, min(48, int(distance / 14)))
        arc = min(distance * 0.08, 60)
        normal_x, normal_y = (-dy / distance, dx / distance) if distance else (0.0, 0.0)
        for i in range(1, steps + 1):
            t = i / steps
            eased = 1 - (1 - t) ** 3
            bend = math.sin(math.pi * eased) * arc
            self.page.mouse.move(start_x + dx * eased + normal_x * bend, start_y + dy * eased + normal_y * bend)
            self.page.wait_for_timeout(self.ms(12))
        self.mouse = (x, y)

    def _approach(self, target: str | dict[str, Any]) -> Locator:
        locator = self.locate(target)
        locator.evaluate("(el, ms) => window.__demo.scrollToElement(el, ms)", None)
        box = locator.bounding_box()
        if box is None:
            raise ValueError(f"{describe_target(target)} has no layout box")
        locator.evaluate("el => window.__demo.track(el)")
        if self.zoom_step:
            self.timeline.focus(Box(box["x"], box["y"], box["width"], box["height"]))
        else:
            self.timeline.wide()
        self._glide_to(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.hold(250)
        return locator

    @contextmanager
    def _awaiting_response(self, fragment: str | None) -> Iterator[None]:
        if not fragment:
            yield
            return
        with self.page.expect_response(lambda response: fragment in response.url, timeout=RESPONSE_TIMEOUT_MS):
            yield
            waiting_from = self.timeline.now()
        self.timeline.idle(waiting_from)

    def _do_goto(self, step: dict[str, Any]) -> None:
        self.timeline.wide()
        waiting_from = self.timeline.now()
        self.page.goto(step["url"], wait_until=self.config.wait_until)
        self.timeline.idle(waiting_from)

    def _do_caption(self, step: dict[str, Any]) -> None:
        self._caption(step["text"])

    def _do_wait(self, step: dict[str, Any]) -> None:
        self.hold(step["ms"])

    def _do_scroll(self, step: dict[str, Any]) -> None:
        self.timeline.wide()
        if "to" in step:
            self.page.evaluate("edge => window.__demo.scrollToEdge(edge)", step["to"])
            return
        locator = self.locate(step["target"])
        locator.evaluate("el => window.__demo.track(el)")
        locator.evaluate("(el, ms) => window.__demo.scrollToElement(el, ms)", None)

    def _do_hover(self, step: dict[str, Any]) -> None:
        self._approach(step["target"])

    def _do_click(self, step: dict[str, Any]) -> None:
        locator = self._approach(step["target"])
        with self._awaiting_response(step.get("waitForResponse")):
            locator.click(delay=80)

    def _do_type(self, step: dict[str, Any]) -> None:
        text = resolve_text(step["text"])
        locator = self._approach(step["target"])
        locator.click(delay=60)
        if step.get("replace"):
            self.hold(200)
            locator.press("ControlOrMeta+a")
            self.hold(250)
            locator.press("Backspace")
            self.hold(200)
        with self._awaiting_response(step.get("waitForResponse")):
            locator.press_sequentially(text, delay=self.ms(step.get("delay", 70)))

    def _do_select(self, step: dict[str, Any]) -> None:
        locator = self._approach(step["target"])
        if "value" in step:
            locator.select_option(value=step["value"])
        else:
            locator.select_option(label=step["label"])

    def _do_press(self, step: dict[str, Any]) -> None:
        locator = self._approach(step["target"]) if "target" in step else None
        with self._awaiting_response(step.get("waitForResponse")):
            if locator:
                locator.press(step["key"])
            else:
                self.page.keyboard.press(step["key"])

    def _do_waitFor(self, step: dict[str, Any]) -> None:
        if "target" in step:
            self.locate(step["target"], timeout=step.get("timeout", TARGET_TIMEOUT_MS))
            return
        fragment = step["response"]
        waiting_from = self.timeline.now()
        self.page.wait_for_response(
            lambda response: fragment in response.url, timeout=step.get("timeout", RESPONSE_TIMEOUT_MS)
        )
        self.timeline.idle(waiting_from)
