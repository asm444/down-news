from unittest.mock import patch, MagicMock
from services.downdetector import DowndetectorScraper

MOCK_HTML = """
<html><body>
<div class="charts-row">
  <script>
    var g_chart_data = [{"x":1710000000,"y":45},{"x":1710000300,"y":890}];
  </script>
</div>
</body></html>
"""


def test_extrai_relatos_recentes():
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = MOCK_HTML
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        scraper = DowndetectorScraper()
        result = scraper.fetch("chatgpt")

    assert result is not None
    assert "reports_1h" in result
    assert isinstance(result["reports_1h"], int)


def test_retorna_none_em_erro():
    with patch("requests.get", side_effect=Exception("blocked")):
        scraper = DowndetectorScraper()
        result = scraper.fetch("chatgpt")
    assert result is None
