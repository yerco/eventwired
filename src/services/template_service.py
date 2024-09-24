from typing import Dict, Type

from src.services.template_engines.jinja_adapter import JinjaAdapter
from src.services.template_engines.mako_adapter import MakoAdapter
from src.services.config_service import ConfigService
from src.services.template_engines.template_engine import TemplateEngine

# Mapping of template engine names to their classes
TEMPLATE_ENGINES: Dict[str, Type[TemplateEngine]] = {
    'JinjaAdapter': JinjaAdapter,
    'MakoAdapter': MakoAdapter,
    # Add other template engines here if needed
}


class TemplateService:
    def __init__(self, config_service: ConfigService = ConfigService()):
        engine_name = config_service.get('TEMPLATE_ENGINE', 'JinjaAdapter')
        engine_class = TEMPLATE_ENGINES.get(engine_name, JinjaAdapter)  # Default to JinjaAdapter if not found
        self.engine = engine_class(template_dir=config_service.get('TEMPLATE_DIR', 'templates'))

    def render_template(self, template_name: str, context: Dict[str, str]) -> str:
        try:
            return self.engine.render(template_name, context)
        except Exception as e:
            return f"Error rendering template: {e}"
