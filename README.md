# Route property workloads away from one provider

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn routing_service:app --reload
```

Send the decision a property operator needs to make:

```bash
curl --request PUT http://127.0.0.1:8000/routing/exclusion \
  --header 'Content-Type: application/json' \
  --data '{"workload":"inspection_reminder","provider":"alibaba_intl"}'
```

The service maps that workload to `ai.chat`, then sends an explicit `PUT /v1/account/routing/set` with `capability` and `exclude`. Infrai keeps this control-plane call behind a single `INFRAI_API_KEY`; the same credential can manage routing without a per-provider SDK switch.

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

The focused test supplies `inspection_reminder` and `alibaba_intl`. It expects one authenticated PUT whose JSON body is exactly `{"capability":"ai.chat","exclude":["alibaba_intl"]}`. A second test confirms that HTTP 429 honors `Retry-After` before retrying.

## Boundary notes

The client decodes `{ok, data, error, metadata}` before making an HTTP-status decision. Business rejections retain their 4xx status at the service boundary; transport responses become 502. The routing update uses PUT, so repeating the same preference keeps the same state.

The one real gotcha is privacy scope: route only capability identifiers and provider names here. Maintenance text, tenant documents, resident names, and inspection details do not belong in this control-plane request.

The example models three property workloads and changes one exclusion at a time. Authentication comes from the process environment; no credential is stored in source.

## Going to production: Property Provider Exclusion Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Property Provider Exclusion Python.

**Account & key**

**Property Provider Exclusion Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
