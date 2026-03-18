import logging
import requests
from typing import Optional
from .base import ServiceAdapter

logger = logging.getLogger("services.microsoft")


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
        except requests.Timeout:
            logger.warning("[%s] Timeout ao consultar %s", self.service_id, url)
        except requests.ConnectionError as e:
            logger.warning("[%s] Erro de conexão: %s", self.service_id, e)
        except requests.HTTPError as e:
            logger.warning("[%s] HTTP %s: %s", self.service_id, e.response.status_code, url)
        except (KeyError, ValueError) as e:
            logger.error("[%s] Resposta inesperada da API: %s", self.service_id, e)
        return None
