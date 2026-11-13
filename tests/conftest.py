from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

import httpx
import pytest

from ayinbox import AsyncAyInbox, AyInbox

FIXTURES = Path(__file__).parent / "fixtures"
INDEX: Dict[str, Any] = json.loads((FIXTURES / "index.json").read_text())
TEST_KEY = "aybox_" + "t" * 43
BASE = "https://api.ayinbox.com/v1"


def load_fixture(ref: str) -> Any:
    """Load ``name.json``, ``name.json[0]`` or ``name.json#key[0]``."""
    match = re.match(r"^([\w./]+\.json)(?:#(\w+))?(?:\[(\d+)\])?$", ref)
    if not match:
        raise ValueError(ref)
    data = json.loads((FIXTURES / match.group(1)).read_text())
    if match.group(2):
        data = data[match.group(2)]
    if match.group(3):
        data = data[int(match.group(3))]
    return data


def error_response(name: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
    meta = INDEX["errors"][f"errors/{name}"]
    merged = dict(meta["headers"])
    merged.update(headers or {})
    return httpx.Response(meta["status"], headers=merged, content=(FIXTURES / "errors" / name).read_bytes())


def _route_regex(path: str) -> "re.Pattern[str]":
    return re.compile("^" + re.sub(r"\\\{\w+\\\}", "[^/]+", re.escape(path)) + "$")


class Route:
    def __init__(self, raw: Dict[str, Any]) -> None:
        self.method: str = raw["method"]
        path: str = raw["path"]
        self.body_rule: Optional[str] = None
        if " (" in path:
            path, rule = path.split(" (", 1)
            self.body_rule = rule.rstrip(")")
        self.query: Dict[str, str] = {}
        if "?" in path:
            path, qs = path.split("?", 1)
            self.query = dict(httpx.QueryParams(qs))
        self.path = path
        self.regex = _route_regex(path)
        self.braces = path.count("{")
        self.status: int = raw["status"]
        self.body: Any = raw["body"]

    def response(self) -> httpx.Response:
        headers = dict(INDEX["default_success_headers"])
        if self.body is None:
            headers.pop("Content-Type", None)
            return httpx.Response(self.status, headers=headers)
        if self.body == "":
            headers.pop("Content-Type", None)
            return httpx.Response(self.status, headers=headers, content=b"")
        payload = self.body if isinstance(self.body, dict) else load_fixture(self.body)
        return httpx.Response(self.status, headers=headers, content=json.dumps(payload).encode())


ROUTES = [Route(r) for r in INDEX["routes"]]

Responder = Union[httpx.Response, Callable[[httpx.Request], httpx.Response], Exception]


class MockAPI:
    """Serves the fixture routes; ``queue`` overrides the next responses in order."""

    def __init__(self) -> None:
        self.requests: List[httpx.Request] = []
        self.queue: List[Responder] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        if self.queue:
            item = self.queue.pop(0)
            if isinstance(item, Exception):
                raise item
            if isinstance(item, httpx.Response):
                return item
            return item(request)
        return self.route(request)

    def route(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        params = dict(request.url.params)
        candidates = [r for r in ROUTES if r.method == request.method and r.regex.match(path)]
        if not candidates:
            return httpx.Response(404, json={"error": "Not Found", "message": "no fixture", "code": "not_found"})
        with_query = [r for r in candidates if r.query and all(params.get(k) == v for k, v in r.query.items())]
        if with_query:
            return with_query[0].response()
        if request.content:
            body = json.loads(request.content)
            if isinstance(body, dict) and len(body.get("campaign_ids") or []) == 1:
                ruled = [r for r in candidates if r.body_rule]
                if ruled:
                    return ruled[0].response()
        plain = sorted((r for r in candidates if not r.query and not r.body_rule), key=lambda r: r.braces)
        return plain[0].response()

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last.content)


@pytest.fixture
def api() -> MockAPI:
    return MockAPI()


@pytest.fixture
def sleeps() -> List[float]:
    return []


@pytest.fixture
def client(api: MockAPI, sleeps: List[float]) -> Iterator[AyInbox]:
    http = httpx.Client(transport=httpx.MockTransport(api.handler))
    c = AyInbox(TEST_KEY, http_client=http)
    c._sleep = sleeps.append
    yield c
    http.close()


def make_async_client(api: MockAPI, sleeps: List[float], **kwargs: Any) -> AsyncAyInbox:
    http = httpx.AsyncClient(transport=httpx.MockTransport(api.handler))
    c = AsyncAyInbox(TEST_KEY, http_client=http, **kwargs)

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    c._sleep = fake_sleep
    return c
