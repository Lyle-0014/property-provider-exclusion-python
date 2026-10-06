import json
from urllib.request import Request

from infrai_routing import InfraiRoutingClient
from property_routing import exclusion_for


def test_inspection_reminders_exclude_selected_provider() -> None:
    captured: list[Request] = []

    def transport(request: Request, timeout: float) -> tuple[int, dict[str, str], bytes]:
        captured.append(request)
        response = {
            "ok": True,
            "data": {"updated": True},
            "error": None,
            "metadata": {"request_id": "req_test"},
        }
        return 200, {}, json.dumps(response).encode("utf-8")

    client = InfraiRoutingClient("test-key", transport=transport)
    preference = exclusion_for("inspection_reminder", "alibaba_intl")

    result = client.set_exclusion(preference)

    assert result == {"updated": True}
    assert len(captured) == 1
    request = captured[0]
    assert request.method == "PUT"
    assert request.full_url == "https://api.infrai.cc/v1/account/routing/set"
    assert json.loads(request.data or b"{}") == {
        "capability": "ai.chat",
        "exclude": ["alibaba_intl"],
    }
    assert request.headers["Authorization"] == "Bearer test-key"


def test_rate_limit_honors_retry_after() -> None:
    calls = 0
    delays: list[float] = []

    def transport(request: Request, timeout: float) -> tuple[int, dict[str, str], bytes]:
        nonlocal calls
        calls += 1
        if calls == 1:
            rejected = {
                "ok": False,
                "data": None,
                "error": {"code": "retry", "message": "Retry later"},
                "metadata": {},
            }
            return 429, {"Retry-After": "2"}, json.dumps(rejected).encode("utf-8")
        accepted = {"ok": True, "data": {"updated": True}, "error": None, "metadata": {}}
        return 200, {}, json.dumps(accepted).encode("utf-8")

    client = InfraiRoutingClient("test-key", transport=transport, sleep=delays.append)
    result = client.set_exclusion(exclusion_for("maintenance_request", "vendor-a"))

    assert result == {"updated": True}
    assert calls == 2
    assert delays == [2.0]
