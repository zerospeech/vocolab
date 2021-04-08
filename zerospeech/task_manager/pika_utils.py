import aio_pika
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import BaseModel

from zerospeech import get_settings

_settings = get_settings(settings_type="queue_worker")


def queue_connection_info():
    """ Build URL to connect to worker queue"""
    _user = _settings.RPC_USERNAME
    _pass = _settings.RPC_USERNAME
    _host = _settings.RPC_HOST
    credentials = pika.credentials.PlainCredentials(
        username=_settings.RPC_USERNAME, password=_settings.RPC_PASSWORD
    )
    if hasattr(_host, "broadcast_address"):
        _host = str(_host.broadcast_address)

    return _host, credentials


def sync_connection_channel() -> BlockingChannel:
    credentials = pika.credentials.PlainCredentials(
        username=_settings.RPC_USERNAME, password=_settings.RPC_PASSWORD
    )
    connection = pika.BlockingConnection(pika.ConnectionParameters(str(_settings.RPC_HOST), credentials=credentials))
    return connection.channel()


async def connection_channel(loop=None) -> (aio_pika.Channel, aio_pika.Connection):
    # todo check on closing connection
    host, credentials = queue_connection_info()
    if loop:
        conn = await aio_pika.connect_robust(
            host=host,
            login=credentials.username, password=credentials.password,
            loop=loop
        )
    else:
        conn = await aio_pika.connect(
            host=host,
            login=credentials.username,
            password=credentials.password
        )

    # Creating channel
    return await conn.channel(), conn


async def message_dispatch(loop, queue_name: str, process_fn):
    channel, conn = await connection_channel(loop)

    # Maximum message count which will be
    # processing at the same time.
    await channel.set_qos(prefetch_count=5)

    # Declaring queue
    queue = await channel.declare_queue(queue_name)

    await queue.consume(process_fn)

    return conn


async def publish_message(msg: BaseModel, queue_name: str, _loop=None):
    channel, _ = await connection_channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=msg.json().encode()),
        routing_key=queue_name,
    )
