from diff_engine import DiffEngine


def test_detecta_novo_incidente():
    previous = {"status": "operational", "incidents": []}
    current = {
        "status": "minor",
        "incidents": [
            {"id": "inc1", "name": "API Slowness", "impact": "minor", "link": ""}
        ],
    }
    engine = DiffEngine()
    changes = engine.diff("claude", previous, current)
    assert len(changes) >= 1
    assert any(c["type"] == "new_incident" for c in changes)


def test_detecta_mudanca_de_status():
    previous = {"status": "operational", "incidents": []}
    current = {"status": "critical", "incidents": []}
    engine = DiffEngine()
    changes = engine.diff("openai", previous, current)
    assert any(c["type"] == "status_change" for c in changes)


def test_sem_mudanca_retorna_lista_vazia():
    state = {"status": "operational", "incidents": []}
    engine = DiffEngine()
    changes = engine.diff("github", state, state)
    assert changes == []


def test_detecta_spike_downdetector():
    previous = {
        "status": "operational",
        "incidents": [],
        "downdetector_br": {"spike_ratio": 1.2},
    }
    current = {
        "status": "operational",
        "incidents": [],
        "downdetector_br": {"spike_ratio": 6.5, "reports_1h": 1200},
    }
    engine = DiffEngine(downdetector_threshold=5.0)
    changes = engine.diff("claude", previous, current)
    assert any(c["type"] == "downdetector_spike" for c in changes)


def test_resolucao_de_incidente():
    previous = {
        "status": "minor",
        "incidents": [{"id": "inc1", "name": "Slowness", "impact": "minor", "link": ""}],
    }
    current = {"status": "operational", "incidents": []}
    engine = DiffEngine()
    changes = engine.diff("openai", previous, current)
    assert any(c["type"] == "resolved" for c in changes)


def test_primeiro_run_sem_historico_nao_gera_mudancas():
    current = {"status": "degraded", "incidents": [{"id": "x", "name": "Test", "impact": "minor", "link": ""}]}
    engine = DiffEngine()
    changes = engine.diff("claude", {}, current)
    assert changes == []
