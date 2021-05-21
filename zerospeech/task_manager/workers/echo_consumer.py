""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""
import asyncio
import os
import random

import aio_pika

from zerospeech import out
from zerospeech.task_manager.model import SimpleLogMessage, message_from_bytes
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker


class EchoWorker(AbstractWorker):

    def __init__(self, *, config):
        super(EchoWorker, self).__init__(config=config)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = message_from_bytes(message.body)
            if not isinstance(br, SimpleLogMessage):
                raise ValueError("Cannot process non LogMessage")

            out.Console.info(f"{os.getpid()} | {br}")

            # add random delay
            await asyncio.sleep(random.randint(10, 100))
