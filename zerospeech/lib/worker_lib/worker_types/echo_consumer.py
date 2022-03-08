""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""
import os

import aio_pika

from zerospeech import out
from zerospeech.db.models.tasks import SimpleLogMessage, message_from_bytes
from .abstract_worker import AbstractWorker


class EchoWorker(AbstractWorker):

    def __init__(self, *, config, server_state):
        super(EchoWorker, self).__init__(config=config, server_state=None)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = message_from_bytes(message.body)
            if not isinstance(br, SimpleLogMessage):
                raise ValueError("Cannot process non LogMessage")

            out.log.info(f"{os.getpid()} | {br}")

            # add random delay
            # await asyncio.sleep(random.randint(10, 100))
