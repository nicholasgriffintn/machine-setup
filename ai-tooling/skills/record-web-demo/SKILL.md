---
name: record-web-demo
description: Records polished, repeatable MP4 (and optional GIF) demo videos of a local or deployed website with Retina capture, automatic zoom onto each interaction, a visible cursor, captions, optional narration and music, an optional browser frame and realistic typing. Runs a short creative brief first (purpose, fun level, voice, music). Use when the user asks for a demo video, screen recording, walkthrough, product demo, PR/release GIF, or "record the site/app doing X".
---

# Record Web Demo

Drive a real Chromium through a JSON script of steps, capture it at Retina resolution, then edit it automatically: the camera zooms onto each interaction and pans back out, long waits are sped through, captions are composited crisply on top, and an optional browser frame adds polish. Output is an H.264 MP4, a contact sheet for review, a `timeline.json` of what happened when, and optionally a GIF. The recorder fails loudly on ambiguous or missing targets, always finalises the browser and always restores files the demo touched.

`SKILL_DIR` below is this skill's directory (for example `~/.claude/skills/record-web-demo`). Run everything from the **target project's root** so restore paths stay inside it:

```bash
uv run --project "$SKILL_DIR/scripts" python "$SKILL_DIR/scripts/record_demo.py" <command> ...
```

## Workflow

- **Confirm the target.** Get the URL and the story to tell (3–8 beats). For a local app, check the dev server is already running; start it only with the project's documented command, and stop it afterwards if you started it.
- **Run the creative brief.** Ask about purpose, fun level, look, narration and music in one round, then let the user hear voice samples and see track options before anything is recorded. Follow [references/brief.md](references/brief.md).
- **Find stable targets.** Run `inspect <url> [--scope main] [--screenshot shot.png]` to print the accessibility tree. Prefer `role` + `name`, then `label`/`placeholder`/`testId`, then CSS. Avoid hashed class names and copy that changes daily. A browser tool you already have works too.
- **Write the config** at `.demo-recording/demo.json`. See [references/config.md](references/config.md) for every step and option. Run `validate .demo-recording/demo.json` until it passes.
- **Prepare the page.** Put logins, cookie dismissals and navigation the viewer should not see in `setup` (runs before capture starts), or reuse a signed-in `storageState`. Remove noise with `hide` (cookie banners, chat widgets, live tickers).
- **Record** with `record .demo-recording/demo.json`. Pass secrets through env vars (`{"env": "DEMO_PASSWORD"}`), never literals in the config.
- **Review before reporting.** Read the `*.contact.png` the command prints (12 evenly spaced frames, times in `contactSheetFrameSeconds`). Check that each beat is visible, captions are readable, the highlight lands on the right element, the zoom frames the action and nothing is cut off. `*.timeline.json` explains odd camera moves. If a moment needs a closer look, extract that frame: `ffmpeg -ss 7.5 -i demo.mp4 -frames:v 1 frame.png`.
- **Iterate.** Adjust `pause`, `speed` or targets and re-record. Narration clips are cached, so re-records do not pay for speech again. Then report the MP4 path, its duration and size, any `musicCredit` the user must publish, and anything you could not show.

## When a step fails

The run stops at the failing step, prints `step N (verb target) failed: reason`, and writes `<output>.failure.png` showing the page at that moment. No video is written and restore files are still put back. Read the screenshot, fix the target (an `nth` for repeated elements, or a narrower scope) and re-run.

## Rules

- **One target, one element.** A target that matches several elements is an error unless you add `nth`. Never guess. Look at the tree again.
- **Demo data only.** Never type real credentials or personal data. Use seed accounts or env vars the user supplies, and say so if the flow needs auth you do not have.
- **Restore what you write.** List files the demo mutates (JSON stores, SQLite files) in `restoreFiles`. Paths must sit inside the working directory. Server-side state that is not a file is the user's to reset, so call it out.
- **Keep artefacts out of git.** Leave `.demo-recording/` uncommitted unless the user asks, and suggest adding it to `.git/info/exclude`.
- **Readable pace.** Aim for 15–60 seconds. Use captions for the "why", not narration of every click. Use `speed` (0.25–4) rather than editing many pauses.
- **Pick the look for the destination.** Defaults (2× capture, auto-zoom, no frame) suit PRs and docs. Add `"frame": true` for launch posts and landing pages. Use `"zoom": false` for QA evidence where the full viewport matters, or `"zoom": false` on a single step to keep that beat wide.

## Setup

First run: `uv sync --project "$SKILL_DIR/scripts"`. Optional keys, read from the environment only: `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` (narration and generated music), and `JAMENDO_CLIENT_ID` (royalty-free tracks, free from devportal.jamendo.com). If Chromium is missing, the recorder falls back to installed Google Chrome. Otherwise run `uv run --project "$SKILL_DIR/scripts" playwright install chromium`. Needs `ffmpeg`/`ffprobe` on PATH (`brew install ffmpeg`).
