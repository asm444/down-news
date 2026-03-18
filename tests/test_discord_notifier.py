import responses
from discord_notifier import DiscordNotifier

WEBHOOKS = {
    "dn-claude": "https://discord.com/api/webhooks/123/abc",
    "dn-geral": "https://discord.com/api/webhooks/456/def",
}

CHANGE_CRITICAL = {
    "type": "status_change",
    "service": "claude",
    "from": "operational",
    "to": "major_outage",
    "critical": True,
}

CHANGE_RESOLVED = {
    "type": "resolved",
    "service": "openai",
    "from": "minor",
    "to": "operational",
    "critical": False,
}


@responses.activate
def test_envia_webhook_para_canal_correto():
    responses.add(responses.POST, WEBHOOKS["dn-claude"], json={}, status=204)
    responses.add(responses.POST, WEBHOOKS["dn-geral"], json={}, status=204)

    notifier = DiscordNotifier(WEBHOOKS, delay=0)
    notifier.notify(
        change=CHANGE_CRITICAL,
        service_config={
            "name": "Claude",
            "discord_channel": "dn-claude",
            "base_url": "https://status.claude.com",
        },
        current_state={"downdetector_br": {"reports_1h": 500, "spike_ratio": 6.0}},
    )
    assert len(responses.calls) == 2


@responses.activate
def test_resolved_envia_apenas_canal_servico():
    responses.add(responses.POST, WEBHOOKS["dn-claude"], json={}, status=204)

    notifier = DiscordNotifier(WEBHOOKS, delay=0)
    notifier.notify(
        change=CHANGE_RESOLVED,
        service_config={
            "name": "OpenAI",
            "discord_channel": "dn-claude",
            "base_url": "https://status.openai.com",
        },
        current_state={},
    )
    assert len(responses.calls) == 1
