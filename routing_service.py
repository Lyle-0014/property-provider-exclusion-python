import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from infrai_routing import InfraiError, InfraiRoutingClient, InfraiTransportError
from property_routing import Workload, exclusion_for


class ProviderExclusionRequest(BaseModel):
    workload: Workload
    provider: str = Field(min_length=1)


class ProviderExclusionResult(BaseModel):
    workload: Workload
    capability: str
    excluded_provider: str
    routing: dict[str, Any]


app = FastAPI(title="Property provider routing")


@app.put("/routing/exclusion", response_model=ProviderExclusionResult)
def set_provider_exclusion(body: ProviderExclusionRequest) -> ProviderExclusionResult:
    preference = exclusion_for(body.workload, body.provider)
    client = InfraiRoutingClient(os.environ.get("INFRAI_API_KEY", ""))
    try:
        routing = client.set_exclusion(preference)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ProviderExclusionResult(
        workload=body.workload,
        capability=preference.capability,
        excluded_provider=preference.exclude[0],
        routing=routing,
    )
