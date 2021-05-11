""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""

import aio_pika

from zerospeech.task_manager.model import BrokerCMD, ExecutorsType, Messenger
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker
from zerospeech import out


class EchoWorker(AbstractWorker):

    def __init__(self, channel_name, logs):
        # todo figure out how logs will be gathered
        super(EchoWorker, self).__init__(channel_name, logs)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = BrokerCMD.from_bytes(message.body)
            if br.executor != ExecutorsType.messenger:
                out.Console.Logger.error("EchoConsumer: cannot handle non message type packets !!")
            else:
                out.Console.info(br.to_str())
