import asyncio
from typing import Any, Dict

import requests
from jinja2 import FileSystemLoader, Environment

from vocolab import settings

_settings = settings.get_settings()


async def notify_mattermost(text: str):
    """ Send a notification to mattermost """
    url = f"{_settings.mattermost_url}/{_settings.MATTERMOST_API_KEY}"
    payload = {
        "channel": _settings.mattermost_channel,
        "username": _settings.mattermost_username,
        "text": text
    }
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, lambda: requests.post(url, json=payload))
    return await future


def render_template(data: Dict[str, Any], template_name: str) -> str:
    """ Render a mattermost message template using values from data"""
    env = Environment(loader=FileSystemLoader(_settings.MATTERMOST_TEMPLATE_DIR))
    template = env.get_template(template_name)
    return template.render(**data)
