from typing import List

CRITICAL_STATUSES = {"critical", "major_outage", "outage"}


class DiffEngine:
    def __init__(self, downdetector_threshold: float = 5.0):
        self.downdetector_threshold = downdetector_threshold

    def diff(self, service_id: str, previous: dict, current: dict) -> List[dict]:
        if not previous:
            return []  # Primeiro run — sem histórico para comparar

        changes = []

        prev_status = previous.get("status", "operational")
        curr_status = current.get("status", "operational")
        if prev_status != curr_status:
            if curr_status == "operational":
                changes.append(
                    {
                        "type": "resolved",
                        "service": service_id,
                        "from": prev_status,
                        "to": curr_status,
                        "critical": False,
                    }
                )
            else:
                changes.append(
                    {
                        "type": "status_change",
                        "service": service_id,
                        "from": prev_status,
                        "to": curr_status,
                        "critical": curr_status in CRITICAL_STATUSES,
                    }
                )

        prev_incident_ids = {i["id"] for i in previous.get("incidents", [])}
        for incident in current.get("incidents", []):
            if incident["id"] not in prev_incident_ids:
                changes.append(
                    {
                        "type": "new_incident",
                        "service": service_id,
                        "incident": incident,
                        "critical": incident.get("impact") in ("critical", "major"),
                    }
                )

        curr_incident_ids = {i["id"] for i in current.get("incidents", [])}
        for incident in previous.get("incidents", []):
            if incident["id"] not in curr_incident_ids and curr_status == "operational":
                changes.append(
                    {
                        "type": "resolved",
                        "service": service_id,
                        "incident": incident,
                        "critical": False,
                    }
                )

        prev_dd = previous.get("downdetector_br", {})
        curr_dd = current.get("downdetector_br", {})
        prev_ratio = prev_dd.get("spike_ratio", 1.0)
        curr_ratio = curr_dd.get("spike_ratio", 1.0)
        if (
            curr_ratio >= self.downdetector_threshold
            and prev_ratio < self.downdetector_threshold
        ):
            changes.append(
                {
                    "type": "downdetector_spike",
                    "service": service_id,
                    "spike_ratio": curr_ratio,
                    "reports_1h": curr_dd.get("reports_1h", 0),
                    "critical": True,
                }
            )

        return changes
