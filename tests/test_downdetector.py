from unittest.mock import patch, MagicMock
from services.downdetector import DowndetectorScraper

MOCK_HTML = """
<html><body>
<script>
  var g_chart_data = [{"x":1710000000,"y":45},{"x":1710000300,"y":890}];
</script>
</body></html>
"""


def _mock_response(html: str = MOCK_HTML, status: int = 200):
    mock = MagicMock()
    mock.text = html
    mock.status_code = status
    mock.raise_for_status = MagicMock()
    return mock


def test_fetch_br_extrai_relatos():
    with patch("requests.get", return_value=_mock_response()):
        scraper = DowndetectorScraper()
        result = scraper.fetch("chatgpt", region="br")
    assert result is not None
    assert "reports_1h" in result
    assert isinstance(result["reports_1h"], int)
    assert result["region"] == "br"


def test_fetch_global_extrai_relatos():
    with patch("requests.get", return_value=_mock_response()):
        scraper = DowndetectorScraper()
        result = scraper.fetch("chatgpt", region="global")
    assert result is not None
    assert result["region"] == "global"


def test_fetch_regiao_desconhecida_retorna_none():
    scraper = DowndetectorScraper()
    result = scraper.fetch("chatgpt", region="fr")
    assert result is None


def test_retorna_none_em_erro_de_conexao():
    with patch("requests.get", side_effect=Exception("blocked")):
        scraper = DowndetectorScraper()
        result = scraper.fetch("chatgpt", region="br")
    assert result is None


def test_fetch_all_regions_retorna_todas_regioes():
    with patch("requests.get", return_value=_mock_response()):
        scraper = DowndetectorScraper()
        result = scraper.fetch_all_regions({"br": "chatgpt", "global": "chatgpt"})
    assert "br" in result
    assert "global" in result


def test_fetch_all_regions_ignora_regiao_sem_slug():
    with patch("requests.get", return_value=_mock_response()):
        scraper = DowndetectorScraper()
        result = scraper.fetch_all_regions({"br": "chatgpt", "global": ""})
    assert "br" in result
    assert "global" not in result


def test_sem_chart_data_retorna_zeros():
    html_sem_dados = "<html><body><p>Sem dados</p></body></html>"
    with patch("requests.get", return_value=_mock_response(html=html_sem_dados)):
        scraper = DowndetectorScraper()
        result = scraper.fetch("netflix", region="br")
    assert result is not None
    assert result["reports_1h"] == 0
    assert result["spike_ratio"] == 1.0
