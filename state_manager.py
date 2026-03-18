import json
import subprocess
from datetime import datetime, timezone

STATE_FILE = "state.json"
STATE_BRANCH = "status-state"


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
            except json.JSONDecodeError:
                self._state = {"last_check": None, "services": {}}
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

        subprocess.run(["git", "fetch", "origin", STATE_BRANCH], check=False)
        subprocess.run(["git", "checkout", STATE_BRANCH], check=True)
        subprocess.run(["git", "add", STATE_FILE], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"state: update {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            ],
            check=False,
        )
        subprocess.run(["git", "push", "origin", STATE_BRANCH], check=False)
        subprocess.run(["git", "checkout", "main"], check=True)
