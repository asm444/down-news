import responses
from services.statuspage import StatuspageAdapter

MOCK_SUMMARY = {
    "status": {"indicator": "minor", "description": "Minor Service Outage"},
    "components": [
        {"name": "API", "status": "degraded_performance", "id": "abc123"},
        {"name": "Web", "status": "operational", "id": "def456"},
    ],
    "incidents": [
        {
            "id": "inc1",
            "name": "API Slowness",
            "status": "investigating",
            "impact": "minor",
            "shortlink": "https://stspg.io/inc1",
        }
    ],
}


@responses.activate
def test_fetch_retorna_status_normalizado():
    responses.add(
        responses.GET,
        "https://status.openai.com/api/v2/summary.json",
        json=MOCK_SUMMARY,
        status=200,
    )
    adapter = StatuspageAdapter("openai", {"base_url": "https://status.openai.com"})
    result = adapter.fetch()
    assert result["status"] == "minor"
    assert result["components"]["API"] == "degraded_performance"
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["name"] == "API Slowness"


@responses.activate
def test_fetch_retorna_none_em_timeout():
    responses.add(
        responses.GET,
        "https://status.openai.com/api/v2/summary.json",
        body=Exception("Connection timeout"),
    )
    adapter = StatuspageAdapter("openai", {"base_url": "https://status.openai.com"})
    result = adapter.fetch()
    assert result is None
