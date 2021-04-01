import aio_pika
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import BaseModel

from zerospeech import get_settings

_settings = get_settings(settings_type="queue_worker")


def queue_url() -> str:
    """ Build URL to connect to worker queue"""
    _user = _settings.RPC_USERNAME
    _pass = _settings.RPC_USERNAME
    _host = _settings.RPC_HOST

    return f"amqp://{_user}:{_pass}@{_host}"


def sync_connection_channel() -> BlockingChannel:
    credentials = pika.credentials.PlainCredentials(
        username=_settings.RPC_USERNAME, password=_settings.RPC_PASSWORD
    )
    connection = pika.BlockingConnection(pika.ConnectionParameters(str(_settings.RPC_HOST), credentials=credentials))
    return connection.channel()


async def async_connection_channel(loop=None):
    if loop:
        conn = await aio_pika.connect_robust(
            queue_url(), loop=loop
        )
    else:
        conn = await aio_pika.connect(queue_url())

    # Creating channel
    return await conn.channel()


async def publish(msg: BaseModel, queue_name: str):
    channel = await async_connection_channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=msg.json().encode()),
        routing_key=queue_name,
    )
