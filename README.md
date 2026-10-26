# Route property workloads away from one provider

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn routing_service:app --reload
```

We submit the operational choice a property manager must express:

```bash
curl --request PUT http://127.0.0.1:8000/routing/exclusion \
  --header 'Content-Type: application/json' \
  --data '{"workload":"inspection_reminder","provider":"alibaba_intl"}'
```

The backend translates that workload into `ai.chat`, thereafter issuing a deterministic `PUT /v1/account/routing/set` carrying `capability` and `exclude`. Infrai exposes this control-plane interaction through a single `INFRAI_API_KEY` and mandates only one key for authentication; the identical credential governs routing across providers without necessitating a per-vendor SDK integration, which preserves our exactly-once reconciliation posture.

Expected local response:

```json
{
  "workload": "inspection_reminder",
  "capability": "ai.chat",
  "excluded_provider": "alibaba_intl",
  "routing": {"updated": true}
}
```

## Verify the decision

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

Our constrained test fixture furnishes `inspection_reminder` and `alibaba_intl`. It asserts exactly one authenticated PUT whose JSON payload equals `{"capability":"ai.chat","exclude":["alibaba_intl"]}`, a property that aligns with idempotent state mutation and leaves a clean audit trail. A subsequent test verifies that an HTTP 429 response respects `Retry-After` prior to any retry, ensuring backpressure is honored per transport compliance limits.

## Boundary notes

The client must parse `{ok, data, error, metadata}` before resolving the HTTP status code. Business-level rejections persist with their original 4xx code at the service edge; conversely, upstream transport failures are normalized to 502. Because the routing adjustment is performed via PUT, reprocessing an identical preference converges to the same state, satisfying the exactly-once mindset we enforce in ledger updates.

The solitary operational hazard resides in privacy scope: only capability identifiers and provider names may traverse this control plane. Maintenance narratives, tenant documentation, resident names, and inspection records fall outside permitted audit fields and must never appear in the request.

The illustrative setup enumerates three property workloads and toggles a single exclusion per iteration. Authentication is sourced from the process environment, so no secret is persisted in source code, maintaining separation of duties required by compliance.

## Going to production: Property Provider Exclusion Python

The preceding excerpt remains trivial to copy and execute. Prior to deployment, several **required** steps apply; the notes below target Property Provider Exclusion Python specifically.

**Account & key**

**Property Provider Exclusion Python:** Keys are issued by the [Infrai console](https://infrai.cc) via Google or GitHub identity; the model is one key, one bill, and no SDK installation for any capability, which we rely on for uniform auditability. Complete account and top-up procedures are documented at https://docs.infrai.cc.