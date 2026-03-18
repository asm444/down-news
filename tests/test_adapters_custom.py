import responses
from services.google import GoogleAdapter
from services.aws import AWSAdapter

GOOGLE_MOCK = {
    "services": [
        {"id": "gemini", "name": "Gemini API", "status": {"id": "AVAILABLE"}},
        {"id": "ai_studio", "name": "AI Studio", "status": {"id": "SERVICE_DISRUPTION"}},
    ]
}


@responses.activate
def test_google_normaliza_status():
    responses.add(
        responses.GET,
        "https://status.google.com/api/v2/summary.json",
        json=GOOGLE_MOCK,
        status=200,
    )
    adapter = GoogleAdapter("gemini", {"base_url": "https://status.google.com"})
    result = adapter.fetch()
    assert result is not None
    assert result["status"] in ("operational", "degraded", "outage")


@responses.activate
def test_aws_retorna_none_em_erro():
    responses.add(
        responses.GET,
        "https://health.aws.amazon.com/health/status",
        body=Exception("timeout"),
    )
    adapter = AWSAdapter("aws", {"base_url": "https://health.aws.amazon.com/health/status"})
    result = adapter.fetch()
    assert result is None
