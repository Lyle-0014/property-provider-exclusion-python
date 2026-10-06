from dataclasses import dataclass
from typing import Literal


Workload = Literal[
    "maintenance_request",
    "tenant_document",
    "inspection_reminder",
]


@dataclass(frozen=True)
class RoutingPreference:
    capability: str
    exclude: list[str]


CAPABILITIES: dict[Workload, str] = {
    "maintenance_request": "property.maintenance_requests",
    "tenant_document": "property.tenant_documents",
    "inspection_reminder": "ai.chat",
}


def exclusion_for(workload: Workload, provider: str) -> RoutingPreference:
    clean_provider = provider.strip()
    if not clean_provider:
        raise ValueError("provider must not be blank")
    return RoutingPreference(
        capability=CAPABILITIES[workload],
        exclude=[clean_provider],
    )
