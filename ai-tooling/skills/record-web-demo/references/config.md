# Demo config reference

Relative paths resolve against the config file's directory. Unknown keys are errors, so typos fail in `validate` rather than mid-recording.

```json
{
  "url": "http://localhost:5173/",
  "output": "checkout.mp4",
  "viewport": { "width": 1440, "height": 900 },
  "speed": 1,
  "colorScheme": "light",
  "waitUntil": "load",
  "gif": { "width": 960, "fps": 12 },
  "zoom": { "max": 1.8 },
  "frame": { "background": ["#0ea5e9", "#6366f1"], "chrome": true },
  "hide": ["#cookie-banner", ".intercom-launcher"],
  "restoreFiles": ["../data/orders.json"],
  "setup": [
    { "do": "click", "target": { "role": "button", "name": "Accept cookies" } }
  ],
  "steps": [
    { "do": "caption", "text": "Checking out as a returning customer" },
    { "do": "click", "target": { "role": "link", "name": "Cart" }, "caption": null },
    { "do": "type", "target": { "label": "Email" }, "text": "demo@example.com", "replace": true },
    { "do": "type", "target": { "label": "Password" }, "text": { "env": "DEMO_PASSWORD" } },
    { "do": "select", "target": { "label": "Delivery" }, "label": "Next day" },
    { "do": "click", "target": { "role": "button", "name": "Place order" }, "waitForResponse": "/api/orders" },
    { "do": "waitFor", "target": { "text": "Order confirmed" } },
    { "do": "hover", "target": { "role": "status" }, "caption": "Confirmation arrives instantly", "pause": 2000 }
  ]
}
```

## Top level

| Key | Default | Notes |
|---|---|---|
| `url` | required | `http(s)` only. Capture starts once it and any `setup` steps have finished. |
| `output` | required | Must end in `.mp4`. The contact sheet, timeline, GIF and failure screenshot are written next to it. |
| `viewport` | 1440×900 | CSS pixels. The video is `viewport × resolution`. 1280×800 suits README embeds. |
| `speed` | 1 | Divides every pause, wait and typing delay. 0.5 is half speed. |
| `colorScheme` | `light` | `light`, `dark` or `no-preference`. |
| `waitUntil` | `load` | Used for the first load and `goto`. Avoid `networkidle` on apps that poll. |
| `gif` | off | `true` or `{ "width", "fps" }`. |
| `restoreFiles` | `[]` | Files snapshotted before the run and restored after, even on failure. Files created during the run are deleted. |
| `setup` | `[]` | Steps run before capture starts, with the same schema as `steps`. |
| `storageState` | none | Playwright storage state file (cookies and localStorage) for a signed-in session. Generate one with `page.context.storage_state(path=...)` against a demo account. |
| `resolution` | 2 | Device pixel ratio for capture and output. 2 gives Retina-sharp text and lossless zoom up to 2×. |
| `fps` | 30 | 24, 30 or 60. |
| `zoom` | `{ "max": 1.8 }` | Auto-zoom onto each interaction. `false` keeps every shot wide. Elements too large to benefit stay wide. |
| `frame` | off | `true` or `{ "background": "#rrggbb" or [from, to], "chrome": bool, "padding": 0–0.2 }`. Wraps the video in a browser window with the live URL on a gradient. |
| `trimWaits` | `true` | Speeds through waits for targets, responses and page loads longer than ~0.7s. |
| `hide` | `[]` | CSS selectors set to `visibility: hidden` on every page. |
| `css` | `""` | Extra CSS injected on every page. Scrollbars are always hidden. |
| `narration` | off | `{ "provider": "say" \| "openai" \| "elevenlabs", "voice", "style"?, "model"?, "fromCaptions"? }`. `style` is delivery instructions for OpenAI. Clips are cached in `.audio-cache/` next to the output. |
| `music` | off | One of `{ "file": "bed.mp3" }`, `{ "jamendo": "<track id>" }` or `{ "generate": "<prompt>" }`, plus `volume` (0–1, default 0.22). Loops to length, fades in and out, and ducks under narration. |

## Steps

Every step has `do` and may add `caption` (a string shows it, `null` hides it; it persists across steps and navigations until changed, and stays fixed while the camera zooms), `pause` (ms to hold afterwards), `zoom: false` (keep this step wide) and `say` (narration for this beat; the step holds until the line finishes).

| `do` | Fields | Default pause |
|---|---|---|
| `caption` | `text` | 1600 |
| `goto` | `url` | 900 |
| `wait` | `ms` | 0 |
| `scroll` | `target` or `to: "top" \| "bottom"` | 500 |
| `hover` | `target` | 800 |
| `click` | `target`, `waitForResponse?` | 800 |
| `type` | `target`, `text`, `replace?`, `delay?` (ms per key, 70), `waitForResponse?` | 700 |
| `select` | `target`, `value` or `label` | 800 |
| `press` | `key` (Playwright key name, such as `Enter` or `ControlOrMeta+k`), `target?`, `waitForResponse?` | 600 |
| `waitFor` | `target` or `response`, `timeout?` (ms) | 300 |

- `waitForResponse` / `response` match the first response whose URL contains the fragment. `waitFor.response` waits for the *next* matching response, so attach `waitForResponse` to the step that triggers the request.
- `text` accepts `{ "env": "NAME" }` to read secrets from the environment.
- Target waits time out after 10s and response waits after 15s.

## Targets

A bare string is a CSS selector. Otherwise use exactly one of these keys:

| Key | Extra keys | Example |
|---|---|---|
| `role` | `name`, `exact` | `{ "role": "button", "name": "Save" }` |
| `label` | `exact` | `{ "label": "Email" }` |
| `placeholder` | `exact` | `{ "placeholder": "Search" }` |
| `text` | `exact` | `{ "text": "Order confirmed" }` |
| `testId` | — | `{ "testId": "cart-total" }` |
| `selector` | — | `{ "selector": "main a[href^='/blog/']" }` |

All of them accept `nth` (0-based). Without `nth`, a target that matches more than one element fails the run. Names match substrings unless `exact` is `true`, so `{ "role": "link", "name": "Blog" }` also matches "Read the blog".
