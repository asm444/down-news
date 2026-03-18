import logging
import requests
from typing import Optional
from .base import ServiceAdapter

logger = logging.getLogger("services.statuspage")


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
