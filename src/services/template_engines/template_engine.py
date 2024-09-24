from abc import ABC, abstractmethod
from typing import Dict


class TemplateEngine(ABC):
    @abstractmethod
    def render(self, template_name: str, context: Dict[str, str]) -> str:
        pass
