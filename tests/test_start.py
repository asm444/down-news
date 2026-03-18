"""Testes do wizard start.py — cobrem lógica interna sem simular input interativo."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import start


def test_slug_hint_normaliza_nome():
    assert start._slug_hint("Netflix") == "netflix"
    assert start._slug_hint("Office 365") == "office-365"
    assert start._slug_hint("AWS S3") == "aws-s3"


def test_sanitize_remove_markdown():
    from discord_notifier import _sanitize
    assert "[link](http://evil.com)" not in _sanitize("[link](http://evil.com)")
    assert "*bold*" not in _sanitize("*bold*")
    assert "`code`" not in _sanitize("`code`")


def test_default_config_estrutura():
    config = start._default_config()
    assert "services" in config
    assert "thresholds" in config
    assert "discord" in config
    assert "channels" in config


def test_get_dd_slugs_formato_novo(monkeypatch):
    """Testa extração de slugs no formato novo (dict com regiões)."""
    import monitor
    svc = {"downdetector": {"br": "chatgpt", "global": "chatgpt"}}
    result = monitor._get_dd_slugs(svc)
    assert result == {"br": "chatgpt", "global": "chatgpt"}


def test_get_dd_slugs_formato_legado(monkeypatch):
    """Testa compatibilidade com formato antigo (downdetector_slug)."""
    import monitor
    svc = {"downdetector_slug": "chatgpt"}
    result = monitor._get_dd_slugs(svc)
    assert result == {"br": "chatgpt"}


def test_get_dd_slugs_sem_downdetector(monkeypatch):
    """Serviço sem Downdetector retorna dict vazio."""
    import monitor
    svc = {"type": "statuspage", "base_url": "https://example.com"}
    result = monitor._get_dd_slugs(svc)
    assert result == {}


def test_get_dd_slugs_ignora_slugs_vazios():
    """Slugs vazios são ignorados."""
    import monitor
    svc = {"downdetector": {"br": "chatgpt", "global": ""}}
    result = monitor._get_dd_slugs(svc)
    assert result == {"br": "chatgpt"}
    assert "global" not in result
