""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""

import aio_pika
from rich.console import Console

from zerospeech.task_manager.model import BrokerCMD, ExecutorsType, Messenger
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker

console = Console()


class EchoWorker(AbstractWorker):

    def __init__(self, channel_name, logs):
        super(EchoWorker, self).__init__(channel_name, logs)

    def eval_message(self, cmd: Messenger):
        """ Evaluate a message type BrokerCMD """
        self.logs.print(cmd.message)
        return cmd.message

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = BrokerCMD.from_bytes(message.body)
            if br.executor != ExecutorsType.messenger:
                console.print("Echo Consumer cannot handle non message type packets !!", style="bold red")
            else:
                msg = self.eval_message(br)
                console.print(msg)

#
# if __name__ == '__main__':
#     # run demo server
#     parser = argparse.ArgumentParser()
#     parser.add_argument('channel_name')
#     args = parser.parse_args()
#     run(args.channel_name)
