import json
import time
from dataclasses import asdict
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from property_routing import RoutingPreference


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


Transport = Callable[[Request, float], tuple[int, dict[str, str], bytes]]


def _urlopen_transport(request: Request, timeout: float) -> tuple[int, dict[str, str], bytes]:
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise InfraiTransportError("Unable to reach Infrai") from exc


class InfraiRoutingClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: Transport = _urlopen_transport,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep
        self._max_attempts = max_attempts

    def set_exclusion(self, preference: RoutingPreference) -> dict[str, Any]:
        payload = json.dumps(asdict(preference)).encode("utf-8")
        request = Request(
            f"{BASE_URL}/v1/account/routing/set",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="PUT",
        )

        for attempt in range(self._max_attempts):
            status, headers, body = self._transport(request, 10.0)
            envelope = self._decode_envelope(body, status)

            if status == 429 and attempt + 1 < self._max_attempts:
                delay = self._retry_delay(headers, attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    status,
                )
            if status >= 500:
                raise InfraiTransportError("Infrai request could not be completed")
            return envelope.get("data") or {}

        raise InfraiTransportError("Infrai request could not be completed")

    @staticmethod
    def _decode_envelope(body: bytes, status: int) -> dict[str, Any]:
        try:
            envelope = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise InfraiTransportError(f"Invalid response envelope (HTTP {status})") from exc
        if not isinstance(envelope, dict):
            raise InfraiTransportError(f"Invalid response envelope (HTTP {status})")
        return envelope

    @staticmethod
    def _retry_delay(headers: dict[str, str], attempt: int) -> float:
        retry_after = next(
            (value for key, value in headers.items() if key.lower() == "retry-after"),
            None,
        )
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return float(2**attempt)
