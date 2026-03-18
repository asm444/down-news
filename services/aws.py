import logging
import requests
from typing import Optional
from .base import ServiceAdapter

logger = logging.getLogger("services.aws")


class AWSAdapter(ServiceAdapter):
    def fetch(self) -> Optional[dict]:
        url = self.config["base_url"]
        try:
            resp = requests.get(url, timeout=10)
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
        except requests.Timeout:
            logger.warning("[%s] Timeout ao consultar %s", self.service_id, url)
        except requests.ConnectionError as e:
            logger.warning("[%s] Erro de conexão: %s", self.service_id, e)
        except requests.HTTPError as e:
            logger.warning("[%s] HTTP %s: %s", self.service_id, e.response.status_code, url)
        except (KeyError, ValueError) as e:
            logger.error("[%s] Resposta inesperada da API: %s", self.service_id, e)
        except Exception as e:
            logger.error("[%s] Erro inesperado: %s", self.service_id, e)
        return None
