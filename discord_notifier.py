import logging
import re
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

COLORS = {
    "critical": 0xFF0000,
    "degraded": 0xFF8C00,
    "maintenance": 0xFFD700,
    "resolved": 0x00C853,
}

BRT = ZoneInfo("America/Sao_Paulo")

logger = logging.getLogger("discord_notifier")

# Caracteres de markdown Discord que podem ser injetados por APIs externas
_MARKDOWN_RE = re.compile(r"[*_`~|<>\[\]()\\]")


def _sanitize(text: str, max_len: int = 200) -> str:
    """Remove markdown Discord e limita tamanho de strings vindas de APIs externas."""
    if not isinstance(text, str):
        return ""
    cleaned = _MARKDOWN_RE.sub("", text)
    return cleaned[:max_len]


class DiscordNotifier:
    def __init__(self, webhooks: dict, delay: float = 1.0):
        self.webhooks = webhooks
        self.delay = delay

    def notify(self, change: dict, service_config: dict, current_state: dict):
        embed = self._build_embed(change, service_config, current_state)
        channel = service_config.get("discord_channel", "dn-geral")
        is_critical = change.get("critical", False)
        content = "@here" if is_critical else ""

        self._send(channel, content, embed)
        time.sleep(self.delay)

        if is_critical and channel != "dn-geral":
            self._send("dn-geral", "@here", embed)
            time.sleep(self.delay)

    def _send(self, channel: str, content: str, embed: dict):
        webhook_url = self.webhooks.get(channel)
        if not webhook_url:
            logger.debug("Webhook não configurado para canal %s — pulando", channel)
            return
        payload = {"content": content, "embeds": [embed]}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code not in (200, 204):
                logger.warning(
                    "Discord retornou status %s para canal %s: %s",
                    resp.status_code,
                    channel,
                    resp.text[:200],
                )
        except requests.Timeout:
            logger.error("Timeout ao enviar webhook para canal %s", channel)
        except requests.ConnectionError as e:
            logger.error("Erro de conexão ao enviar webhook para %s: %s", channel, e)
        except Exception as e:
            logger.error("Erro inesperado ao enviar webhook para %s: %s", channel, e)

    def _build_embed(
        self, change: dict, service_config: dict, current_state: dict
    ) -> dict:
        now_brt = datetime.now(BRT).strftime("%H:%M BRT")
        change_type = change.get("type", "")
        # service_name vem de config local (confiável), não de API externa
        service_name = service_config.get("name", change["service"])
        # base_url vem de config local (confiável)
        base_url = service_config.get("base_url", "")
        dd = current_state.get("downdetector_br", {})

        if change_type == "resolved":
            title = f"🟢 [RESOLVIDO] {service_name} — Serviço normalizado"
            color = COLORS["resolved"]
            from_status = _sanitize(change.get("from", "degraded"))
            description = (
                f"⏱ Status anterior: `{from_status}`\n"
                f"🕐 Resolvido: {now_brt}"
            )

        elif change_type == "downdetector_spike":
            title = f"🔴 [SPIKE BR] {service_name} — Alto volume de relatos"
            color = COLORS["critical"]
            description = (
                f"📣 Relatos na última hora: **{int(dd.get('reports_1h', 0))}**\n"
                f"📊 Spike: **{change.get('spike_ratio', 0):.1f}x** acima do normal\n"
                f"🕐 Detectado: {now_brt}"
            )

        elif change_type in ("status_change", "new_incident"):
            is_critical = change.get("critical", False)
            label = "CRÍTICO" if is_critical else "DEGRADADO"
            icon = "🔴" if is_critical else "🟠"
            title = f"{icon} [{label}] {service_name}"
            color = COLORS["critical"] if is_critical else COLORS["degraded"]

            # Dados de incidentes vêm de API externa — sanitizar
            incident = change.get("incident", {})
            incident_name = _sanitize(incident.get("name", ""))
            from_status = _sanitize(change.get("from", "?"))
            to_status = _sanitize(change.get("to", "?"))

            lines = [
                f"📊 Status: `{from_status}` → `{to_status}`",
                f"🕐 Detectado: {now_brt}",
            ]
            if incident_name:
                lines.insert(0, f"📍 Incidente: {incident_name}")
            if dd.get("reports_1h"):
                spike_pct = (dd.get("spike_ratio", 1) - 1) * 100
                lines.append(
                    f"📣 Downdetector BR: **{int(dd['reports_1h'])}** relatos"
                    f" (+{spike_pct:.0f}%)"
                )
            if base_url:
                lines.append(f"🔗 {base_url}")
            description = "\n".join(lines)

        else:
            title = f"ℹ️ {service_name} — Atualização"
            color = 0x7289DA
            description = _sanitize(str(change), max_len=500)

        return {"title": title[:256], "description": description[:4096], "color": color}
