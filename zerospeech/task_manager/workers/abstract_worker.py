import asyncio
import abc

import aio_pika
from zerospeech.task_manager.pika_utils import message_dispatch


class AbstractWorker(abc.ABC):

    def __init__(self, channel_name, logs):
        self.channel_name = channel_name
        self.logs = logs
        self.loop = asyncio.get_event_loop()

    @abc.abstractmethod
    async def _processor(self, message: aio_pika.IncomingMessage):
        raise NotImplemented("method is not implemented in abstract class")

    def run(self):
        """ Run Message Broker """
        main_loop = asyncio.get_event_loop()
        connection = main_loop.run_until_complete(
            message_dispatch(main_loop, self.channel_name, self._processor)
        )
        try:
            main_loop.run_forever()
        finally:
            main_loop.run_until_complete(connection.close())
