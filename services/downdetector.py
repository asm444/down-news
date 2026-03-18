import json
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("services.downdetector")


class DowndetectorScraper:
    BASE_URL = "https://downdetector.com.br/status/{slug}/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    def fetch(self, slug: str) -> Optional[dict]:
        url = self.BASE_URL.format(slug=slug)
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            match = re.search(
                r"var g_chart_data\s*=\s*(\[.*?\]);", resp.text, re.DOTALL
            )
            if not match:
                logger.debug("[downdetector/%s] g_chart_data não encontrado na página", slug)
                return {"reports_1h": 0, "baseline": 0.0, "spike_ratio": 1.0}

            data_points = json.loads(match.group(1))
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(hours=24)

            reports_1h = sum(
                p["y"]
                for p in data_points
                if datetime.fromtimestamp(p["x"], tz=timezone.utc) >= one_hour_ago
            )
            reports_24h = sum(
                p["y"]
                for p in data_points
                if datetime.fromtimestamp(p["x"], tz=timezone.utc) >= one_day_ago
            )
            baseline = reports_24h / 24 if reports_24h else 1
            spike_ratio = reports_1h / baseline if baseline > 0 else 1.0

            return {
                "reports_1h": int(reports_1h),
                "baseline": round(baseline, 1),
                "spike_ratio": round(spike_ratio, 2),
            }
        except requests.Timeout:
            logger.warning("[downdetector/%s] Timeout ao consultar página", slug)
        except requests.ConnectionError as e:
            logger.warning("[downdetector/%s] Erro de conexão: %s", slug, e)
        except requests.HTTPError as e:
            logger.warning(
                "[downdetector/%s] HTTP %s (possível bloqueio de scraping)",
                slug,
                e.response.status_code,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("[downdetector/%s] Erro ao parsear dados: %s", slug, e)
        except Exception as e:
            logger.error("[downdetector/%s] Erro inesperado: %s", slug, e)
        return None
