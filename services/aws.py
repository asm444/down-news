import requests
from typing import Optional
from .base import ServiceAdapter


class AWSAdapter(ServiceAdapter):
    def fetch(self) -> Optional[dict]:
        try:
            resp = requests.get(self.config["base_url"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            events = data.get("events", [])
            active = [e for e in events if e.get("statusCode") != "closed"]
            status = "operational" if not active else "degraded"
            return {
                "status": status,
                "description": f"{len(active)} evento(s) ativo(s)",
                "components": {},
                "incidents": [
                    {
                        "id": e["arn"],
                        "name": e.get("eventTypeCode", ""),
                        "status": e.get("statusCode", ""),
                        "impact": "unknown",
                        "link": "",
                    }
                    for e in active[:5]
                ],
            }
        except Exception:
            return None
