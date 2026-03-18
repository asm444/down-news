import os
import yaml
from state_manager import StateManager
from diff_engine import DiffEngine
from discord_notifier import DiscordNotifier
from services.statuspage import StatuspageAdapter
from services.google import GoogleAdapter
from services.microsoft import MicrosoftAdapter
from services.aws import AWSAdapter
from services.downdetector import DowndetectorScraper

ADAPTER_MAP = {
    "statuspage": StatuspageAdapter,
    "google": GoogleAdapter,
    "google_cloud": GoogleAdapter,
    "microsoft": MicrosoftAdapter,
    "azure": MicrosoftAdapter,
    "aws": AWSAdapter,
}


def load_config(path: str = "config.yml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_webhooks() -> dict:
    channels = [
        "dn-claude", "dn-openai", "dn-gemini",
        "dn-microsoft", "dn-cloud", "dn-dev", "dn-geral",
    ]
    return {
        ch: url
        for ch in channels
        if (url := os.environ.get(f"DISCORD_WEBHOOK_{ch.upper().replace('-', '_')}"))
    }


def run_monitor():
    config = load_config()
    sm = StateManager()
    sm.load()

    thresholds = config.get("thresholds", {})
    dd_threshold = thresholds.get("downdetector_spike_ratio", 5.0)
    delay = config.get("discord", {}).get("delay_between_webhooks", 1)

    engine = DiffEngine(downdetector_threshold=dd_threshold)
    notifier = DiscordNotifier(build_webhooks(), delay=delay)
    dd_scraper = DowndetectorScraper()

    for service_id, svc_config in config.get("services", {}).items():
        adapter_class = ADAPTER_MAP.get(svc_config["type"])
        if not adapter_class:
            continue

        adapter = adapter_class(service_id, svc_config)
        current = adapter.fetch()
        if current is None:
            continue

        dd_slug = svc_config.get("downdetector_slug")
        if dd_slug:
            dd_data = dd_scraper.fetch(dd_slug)
            if dd_data:
                current["downdetector_br"] = dd_data

        previous = sm.get_service(service_id)
        changes = engine.diff(service_id, previous, current)

        for change in changes:
            notifier.notify(change, svc_config, current)

        sm.update_service(service_id, current)

    sm.save()


if __name__ == "__main__":
    run_monitor()
