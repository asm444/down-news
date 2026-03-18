import requests
from typing import Optional
from .base import ServiceAdapter


class StatuspageAdapter(ServiceAdapter):
    def fetch(self) -> Optional[dict]:
        url = f"{self.config['base_url']}/api/v2/summary.json"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {
                "status": data["status"]["indicator"],
                "description": data["status"]["description"],
                "components": {
                    c["name"]: c["status"] for c in data.get("components", [])
                },
                "incidents": [
                    {
                        "id": inc["id"],
                        "name": inc["name"],
                        "status": inc["status"],
                        "impact": inc["impact"],
                        "link": inc.get("shortlink", ""),
                    }
                    for inc in data.get("incidents", [])
                ],
            }
        except Exception:
            return None
