import abc
import asyncio
from typing import Optional

import aio_pika

from zerospeech.task_manager.config import Config, ServerState
from zerospeech.task_manager import pika_utils


async def check_tasks():
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    for t in tasks:
        print(t.get_coro())


class AbstractWorker(abc.ABC):

    def __init__(self, *, config: Config, server_state: Optional[ServerState]):
        self.channel_name = config.channel
        self.prefetch_count = config.prefetch_count
        self.server_state = server_state

    @abc.abstractmethod
    async def _processor(self, message: aio_pika.IncomingMessage):
        raise NotImplemented("method is not implemented in abstract class")

    async def run(self, *, loop=None):
        """ Run Message Broker """
        if loop is None:
            loop = asyncio.get_running_loop()

        channel, conn = await pika_utils.connection_channel(loop)

        await channel.set_qos(prefetch_count=self.prefetch_count)

        # Declaring queue
        queue = await channel.declare_queue(self.channel_name)

        await queue.consume(self._processor)



