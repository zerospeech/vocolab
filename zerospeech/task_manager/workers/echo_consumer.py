""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""
import asyncio
import os
import random

import aio_pika

from zerospeech import out
from zerospeech.task_manager.model import BrokerCMD, ExecutorsType
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker


class EchoWorker(AbstractWorker):

    def __init__(self, *, config):
        super(EchoWorker, self).__init__(config=config)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = BrokerCMD.from_bytes(message.body)
            if br.executor != ExecutorsType.messenger:
                out.Console.Logger.error("EchoConsumer: cannot handle non message type packets !!")
            else:
                out.Console.info(f"{os.getpid()} | {br.to_str()}")

            # add random delay
            await asyncio.sleep(random.randint(10, 100))
