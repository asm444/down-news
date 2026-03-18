import logging
import requests
from typing import Optional
from .base import ServiceAdapter

logger = logging.getLogger("services.google")

STATUS_MAP = {
    "AVAILABLE": "operational",
    "SERVICE_INFORMATION": "operational",
    "SERVICE_DISRUPTION": "degraded",
    "SERVICE_OUTAGE": "outage",
}


class GoogleAdapter(ServiceAdapter):
    def fetch(self) -> Optional[dict]:
        url = f"{self.config['base_url']}/api/v2/summary.json"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            services = data.get("services", [])
            statuses = [STATUS_MAP.get(s["status"]["id"], "unknown") for s in services]
            if "outage" in statuses:
                overall = "outage"
            elif "degraded" in statuses:
                overall = "degraded"
            else:
                overall = "operational"
            return {
                "status": overall,
                "description": f"{sum(1 for s in statuses if s != 'operational')} serviço(s) afetado(s)",
                "components": {
                    s["name"]: STATUS_MAP.get(s["status"]["id"], "unknown")
                    for s in services
                },
                "incidents": [],
            }
        except requests.Timeout:
            logger.warning("[%s] Timeout ao consultar %s", self.service_id, url)
        except requests.ConnectionError as e:
            logger.warning("[%s] Erro de conexão: %s", self.service_id, e)
        except requests.HTTPError as e:
            logger.warning("[%s] HTTP %s: %s", self.service_id, e.response.status_code, url)
        except (KeyError, ValueError) as e:
            logger.error("[%s] Resposta inesperada da API: %s", self.service_id, e)
        return None
