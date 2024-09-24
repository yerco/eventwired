from mako.lookup import TemplateLookup
from typing import Dict

from src.services.template_engines.template_engine import TemplateEngine


class MakoAdapter(TemplateEngine):
    def __init__(self, template_dir: str):
        self.lookup = TemplateLookup(directories=[template_dir])

    def render(self, template_name: str, context: Dict[str, str]) -> str:
        template = self.lookup.get_template(template_name)
        return template.render(**context)
