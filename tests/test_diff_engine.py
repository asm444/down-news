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


def test_detecta_spike_downdetector_br():
    previous = {
        "status": "operational",
        "incidents": [],
        "downdetector": {"br": {"spike_ratio": 1.2, "reports_1h": 10}},
    }
    current = {
        "status": "operational",
        "incidents": [],
        "downdetector": {"br": {"spike_ratio": 6.5, "reports_1h": 1200}},
    }
    engine = DiffEngine(downdetector_threshold=5.0)
    changes = engine.diff("claude", previous, current)
    spike = next((c for c in changes if c["type"] == "downdetector_spike"), None)
    assert spike is not None
    assert spike["region"] == "br"
    assert spike["critical"] is True


def test_detecta_spike_downdetector_global():
    previous = {
        "status": "operational",
        "incidents": [],
        "downdetector": {"global": {"spike_ratio": 1.0, "reports_1h": 5}},
    }
    current = {
        "status": "operational",
        "incidents": [],
        "downdetector": {"global": {"spike_ratio": 8.0, "reports_1h": 3000}},
    }
    engine = DiffEngine(downdetector_threshold=5.0)
    changes = engine.diff("chatgpt", previous, current)
    spike = next((c for c in changes if c["type"] == "downdetector_spike"), None)
    assert spike is not None
    assert spike["region"] == "global"


def test_detecta_spikes_em_multiplas_regioes():
    previous = {
        "status": "operational",
        "incidents": [],
        "downdetector": {
            "br": {"spike_ratio": 1.0},
            "global": {"spike_ratio": 1.0},
        },
    }
    current = {
        "status": "operational",
        "incidents": [],
        "downdetector": {
            "br": {"spike_ratio": 7.0, "reports_1h": 900},
            "global": {"spike_ratio": 6.0, "reports_1h": 5000},
        },
    }
    engine = DiffEngine(downdetector_threshold=5.0)
    changes = engine.diff("openai", previous, current)
    spikes = [c for c in changes if c["type"] == "downdetector_spike"]
    assert len(spikes) == 2
    regions = {s["region"] for s in spikes}
    assert regions == {"br", "global"}


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
    current = {"status": "degraded", "incidents": []}
    engine = DiffEngine()
    changes = engine.diff("claude", {}, current)
    assert changes == []
