import requests
from typing import Optional
from .base import ServiceAdapter


class MicrosoftAdapter(ServiceAdapter):
    def fetch(self) -> Optional[dict]:
        url = f"{self.config['base_url']}/api/MSCommerce/2016/cloud/products"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            workloads = data.get("WorkloadStatus", [])
            has_incident = any(
                w.get("StatusDisplayName", "") not in ("Normal service", "")
                for w in workloads
            )
            status = "degraded" if has_incident else "operational"
            return {
                "status": status,
                "description": "Microsoft 365 Services",
                "components": {
                    w["WorkloadDisplayName"]: (
                        "operational"
                        if w.get("StatusDisplayName") == "Normal service"
                        else "degraded"
                    )
                    for w in workloads
                },
                "incidents": [],
            }
        except Exception:
            return None
