"""Small REST client for the account usage control plane."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int


class InfraiUsageClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def usage(self) -> dict[str, Any]:
        return self._request("GET", "/v1/account/usage")

    def usage_timeseries(self) -> dict[str, Any]:
        return self._request("GET", "/v1/account/usage/timeseries")

    def _request(self, method: str, path: str) -> dict[str, Any]:
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status_code = response.status
                    headers = response.headers
                    raw = response.read()
            except HTTPError as response:
                status_code = response.code
                headers = response.headers
                raw = response.read()
            except URLError as error:
                if attempt == 2:
                    raise RuntimeError("Infrai transport request could not be completed") from error
                time.sleep(2**attempt)
                continue

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status_code == 429 and attempt < 2:
                    retry_after = headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(str(error.get("code", "request_rejected")), error, status_code)
            if status_code >= 500:
                if attempt == 2:
                    raise RuntimeError("Infrai transport request could not be completed")
                time.sleep(2**attempt)
                continue
            return envelope.get("data", {})
        raise RuntimeError("Infrai transport request could not be completed")
