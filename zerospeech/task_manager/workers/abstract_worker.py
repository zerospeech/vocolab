import asyncio
import abc

import aio_pika
from zerospeech.task_manager.pika_utils import message_dispatch


class AbstractWorker(abc.ABC):

    def __init__(self, channel_name, logs):
        self.channel_name = channel_name
        self.logs = logs

    @abc.abstractmethod
    async def _processor(self, message: aio_pika.IncomingMessage):
        raise NotImplemented("method is not implemented in abstract class")

    def run(self, loop):
        """ Run Message Broker """
        connection = loop.run_until_complete(
            message_dispatch(loop, self.channel_name, self._processor)
        )
        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(connection.close())
