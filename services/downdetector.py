import json
import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("services.downdetector")

REGIONS = {
    "br": "https://downdetector.com.br/status/{slug}/",
    "global": "https://downdetector.com/status/{slug}/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


class DowndetectorScraper:
    def fetch(self, slug: str, region: str = "br") -> Optional[dict]:
        """
        Consulta o Downdetector para um serviço.

        Args:
            slug: slug do serviço na URL (ex: "chatgpt")
            region: "br" (downdetector.com.br) ou "global" (downdetector.com)
        """
        base = REGIONS.get(region)
        if not base:
            logger.error("Região desconhecida: %s (use 'br' ou 'global')", region)
            return None

        url = base.format(slug=slug)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            match = re.search(
                r"var g_chart_data\s*=\s*(\[.*?\]);", resp.text, re.DOTALL
            )
            if not match:
                logger.debug("[downdetector/%s/%s] g_chart_data não encontrado", region, slug)
                return {"reports_1h": 0, "baseline": 0.0, "spike_ratio": 1.0, "region": region}

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
                "region": region,
            }
        except requests.Timeout:
            logger.warning("[downdetector/%s/%s] Timeout", region, slug)
        except requests.ConnectionError as e:
            logger.warning("[downdetector/%s/%s] Erro de conexão: %s", region, slug, e)
        except requests.HTTPError as e:
            logger.warning(
                "[downdetector/%s/%s] HTTP %s (possível bloqueio)",
                region, slug, e.response.status_code,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("[downdetector/%s/%s] Erro ao parsear: %s", region, slug, e)
        except Exception as e:
            logger.error("[downdetector/%s/%s] Erro inesperado: %s", region, slug, e)
        return None

    def fetch_all_regions(self, slugs: dict) -> dict:
        """
        Consulta múltiplas regiões para o mesmo serviço.

        Args:
            slugs: dict com região → slug. Ex: {"br": "chatgpt", "global": "chatgpt"}

        Returns:
            dict com região → resultado. Ex: {"br": {...}, "global": {...}}
        """
        results = {}
        for region, slug in slugs.items():
            if slug:
                data = self.fetch(slug, region)
                if data:
                    results[region] = data
        return results
