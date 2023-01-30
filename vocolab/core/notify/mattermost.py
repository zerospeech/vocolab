import asyncio
from typing import Any, Dict

import requests
from jinja2 import FileSystemLoader, Environment

from vocolab import settings

_settings = settings.get_settings()


async def notify_mattermost(text: str):
    """ Send a notification to mattermost """
    url = f"{_settings.notify_options.MATTERMOST_URL}/{_settings.notify_options.MATTERMOST_API_KEY}"
    payload = {
        "channel": _settings.notify_options.MATTERMOST_CHANNEL,
        "username": _settings.notify_options.MATTERMOST_USERNAME,
        "text": text
    }
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, lambda: requests.post(url, json=payload))
    return await future


def render_template(data: Dict[str, Any], template_name: str) -> str:
    """ Render a mattermost message template using values from data"""
    env = Environment(loader=FileSystemLoader(_settings.mattermost_templates_dir))
    template = env.get_template(template_name)
    return template.render(**data)
