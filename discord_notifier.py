import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

ICONS = {
    "status_change_critical": "🔴",
    "status_change": "🟠",
    "maintenance": "🟡",
    "resolved": "🟢",
    "downdetector_spike": "🔴",
    "new_incident": "🟠",
}

COLORS = {
    "critical": 0xFF0000,
    "degraded": 0xFF8C00,
    "maintenance": 0xFFD700,
    "resolved": 0x00C853,
}

BRT = ZoneInfo("America/Sao_Paulo")


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
            return
        payload = {"content": content, "embeds": [embed]}
        try:
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception:
            pass

    def _build_embed(
        self, change: dict, service_config: dict, current_state: dict
    ) -> dict:
        now_brt = datetime.now(BRT).strftime("%H:%M BRT")
        change_type = change.get("type", "")
        service_name = service_config.get("name", change["service"])
        base_url = service_config.get("base_url", "")
        dd = current_state.get("downdetector_br", {})

        if change_type == "resolved":
            title = f"🟢 [RESOLVIDO] {service_name} — Serviço normalizado"
            color = COLORS["resolved"]
            description = (
                f"⏱ Status anterior: `{change.get('from', 'degraded')}`\n"
                f"🕐 Resolvido: {now_brt}"
            )

        elif change_type == "downdetector_spike":
            title = f"🔴 [SPIKE BR] {service_name} — Alto volume de relatos"
            color = COLORS["critical"]
            description = (
                f"📣 Relatos na última hora: **{dd.get('reports_1h', 0)}**\n"
                f"📊 Spike: **{change.get('spike_ratio', 0):.1f}x** acima do normal\n"
                f"🕐 Detectado: {now_brt}"
            )

        elif change_type in ("status_change", "new_incident"):
            is_critical = change.get("critical", False)
            label = "CRÍTICO" if is_critical else "DEGRADADO"
            icon = "🔴" if is_critical else "🟠"
            title = f"{icon} [{label}] {service_name}"
            color = COLORS["critical"] if is_critical else COLORS["degraded"]
            incident = change.get("incident", {})
            lines = [
                f"📊 Status: `{change.get('from', '?')}` → `{change.get('to', '?')}`",
                f"🕐 Detectado: {now_brt}",
            ]
            if incident.get("name"):
                lines.insert(0, f"📍 Incidente: {incident['name']}")
            if dd.get("reports_1h"):
                spike_pct = (dd.get("spike_ratio", 1) - 1) * 100
                lines.append(
                    f"📣 Downdetector BR: **{dd['reports_1h']}** relatos (+{spike_pct:.0f}%)"
                )
            if base_url:
                lines.append(f"🔗 {base_url}")
            description = "\n".join(lines)

        else:
            title = f"ℹ️ {service_name} — Atualização"
            color = 0x7289DA
            description = str(change)

        return {"title": title, "description": description, "color": color}
