from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class HttpError(RuntimeError):
    pass


def request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 180,
) -> bytes:
    data = json.dumps(body).encode() if body is not None else None
    all_headers = {"User-Agent": "record-web-demo", **(headers or {})}
    if data is not None:
        all_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=all_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read()[:400].decode(errors="replace")
        raise HttpError(f"{method} {url.split('?')[0]} returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise HttpError(f"{method} {url.split('?')[0]} failed: {error.reason}") from error


def request_json(url: str, **kwargs: Any) -> Any:
    return json.loads(request(url, **kwargs))
