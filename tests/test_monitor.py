from unittest.mock import patch, MagicMock


def test_monitor_sem_mudancas_nao_envia_webhook():
    state_operacional = {
        "status": "operational",
        "incidents": [],
        "downdetector_br": {"spike_ratio": 1.0},
    }

    mock_config = {
        "services": {
            "claude": {
                "name": "Claude",
                "type": "statuspage",
                "base_url": "https://status.claude.com",
                "discord_channel": "dn-claude",
                "downdetector_slug": "chatbot-anthropic",
            }
        },
        "thresholds": {
            "downdetector_spike_ratio": 5.0,
            "downdetector_baseline_hours": 24,
            "request_timeout": 10,
            "retry_attempts": 3,
            "retry_backoff": 2,
        },
        "discord": {
            "mention": "@here",
            "timezone": "America/Sao_Paulo",
            "delay_between_webhooks": 0,
        },
    }

    with patch("monitor.load_config", return_value=mock_config), \
         patch("monitor.StateManager") as MockSM, \
         patch("monitor.DiscordNotifier") as MockDN, \
         patch("monitor.DiffEngine") as MockDE, \
         patch("monitor.StatuspageAdapter") as MockAdapter, \
         patch("monitor.DowndetectorScraper") as MockDD:

        mock_sm = MockSM.return_value
        mock_sm.load.return_value = {"last_check": None, "services": {}}
        mock_sm.get_service.return_value = state_operacional

        MockDE.return_value.diff.return_value = []
        MockAdapter.return_value.fetch.return_value = state_operacional
        MockDD.return_value.fetch.return_value = {
            "reports_1h": 5, "baseline": 5, "spike_ratio": 1.0
        }

        from monitor import run_monitor
        run_monitor()

        MockDN.return_value.notify.assert_not_called()
