from unittest.mock import patch, MagicMock
from state_manager import StateManager

MOCK_STATE = {
    "last_check": "2026-03-18T14:00:00Z",
    "services": {
        "claude": {
            "status": "operational",
            "incidents": [],
            "downdetector_br": {"reports_1h": 5},
        }
    },
}


def test_load_retorna_estado_vazio_se_arquivo_nao_existe():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        sm = StateManager()
        state = sm.load()
    assert state == {"last_check": None, "services": {}}


def test_get_service_retorna_dict_vazio_para_servico_novo():
    sm = StateManager()
    sm._state = MOCK_STATE
    result = sm.get_service("novo_servico")
    assert result == {}


def test_get_service_retorna_estado_existente():
    sm = StateManager()
    sm._state = MOCK_STATE
    result = sm.get_service("claude")
    assert result["status"] == "operational"
