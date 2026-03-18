import json
import logging
import subprocess
from datetime import datetime, timezone

STATE_FILE = "state.json"
STATE_BRANCH = "status-state"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("state_manager")


class StateManager:
    def __init__(self):
        self._state: dict = {"last_check": None, "services": {}}

    def load(self) -> dict:
        result = subprocess.run(
            ["git", "show", f"{STATE_BRANCH}:{STATE_FILE}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            try:
                self._state = json.loads(result.stdout)
                logger.info("state.json carregado do branch %s", STATE_BRANCH)
            except json.JSONDecodeError as e:
                logger.error("state.json corrompido, reiniciando estado: %s", e)
                self._state = {"last_check": None, "services": {}}
        else:
            logger.warning(
                "Não foi possível ler state.json (%s), usando estado vazio",
                STATE_BRANCH,
            )
        return self._state

    def get_service(self, service_id: str) -> dict:
        return self._state.get("services", {}).get(service_id, {})

    def update_service(self, service_id: str, data: dict):
        if "services" not in self._state:
            self._state["services"] = {}
        self._state["services"][service_id] = data

    def save(self):
        self._state["last_check"] = datetime.now(timezone.utc).isoformat()

        with open(STATE_FILE, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)

        try:
            subprocess.run(
                ["git", "fetch", "origin", STATE_BRANCH],
                capture_output=True,
                check=False,  # fetch pode falhar se remoto ainda não existe
            )
            subprocess.run(
                ["git", "checkout", STATE_BRANCH],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "add", STATE_FILE],
                capture_output=True,
                check=True,
            )
            result = subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"state: update {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
                ],
                capture_output=True,
                text=True,
                check=False,  # retorna 1 se não há mudanças — comportamento esperado
            )
            if result.returncode not in (0, 1):
                logger.error("git commit falhou: %s", result.stderr.strip())

            push = subprocess.run(
                ["git", "push", "origin", STATE_BRANCH],
                capture_output=True,
                text=True,
                check=False,
            )
            if push.returncode != 0:
                logger.error("git push falhou: %s", push.stderr.strip())
            else:
                logger.info("state.json salvo e enviado ao branch %s", STATE_BRANCH)

        except subprocess.CalledProcessError as e:
            logger.error(
                "Operação git falhou (cmd=%s): %s",
                " ".join(e.cmd),
                e.stderr,
            )
        finally:
            subprocess.run(
                ["git", "checkout", "main"],
                capture_output=True,
                check=False,
            )
