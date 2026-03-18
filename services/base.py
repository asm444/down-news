from abc import ABC, abstractmethod
from typing import Optional


class ServiceAdapter(ABC):
    def __init__(self, service_id: str, config: dict):
        self.service_id = service_id
        self.config = config

    @abstractmethod
    def fetch(self) -> Optional[dict]:
        """Retorna dict normalizado ou None se falhar."""
        pass
