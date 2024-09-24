import os

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class JinjaAdapter:
    def __init__(self, template_dir='templates'):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, template_path: str, context: dict) -> str:
        try:
            # If the template_path is an absolute path, load it directly
            if os.path.isabs(template_path):
                # Create a temporary FileSystemLoader for the specific template file
                template_loader = FileSystemLoader(os.path.dirname(template_path))
                template_env = Environment(loader=template_loader)
                template = template_env.get_template(os.path.basename(template_path))
            else:
                # If it's a relative path, use the standard environment loader
                template = self.env.get_template(template_path)
            return template.render(context)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_path}' not found.")
