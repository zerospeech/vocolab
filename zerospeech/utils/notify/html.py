from typing import Dict, Any

from jinja2 import FileSystemLoader, Environment

from zerospeech import settings

_settings = settings.get_settings()


def generate_html_response(data: Dict[str, Any], template_name: str) -> str:
    """ Render an html template using values from data"""
    env = Environment(loader=FileSystemLoader(_settings.HTML_TEMPLATE_DIR))
    template = env.get_template(template_name)
    return template.render(**data)
