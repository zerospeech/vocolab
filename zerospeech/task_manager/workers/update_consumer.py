import aio_pika

from zerospeech import exc, out
from zerospeech.task_manager.model import BrokerCMD, Function, ExecutorsType
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker
from zerospeech.utils import update_tasks


class UpdateTaskWorker(AbstractWorker):

    def __init__(self, channel_name, logs):
        super(UpdateTaskWorker, self).__init__(channel_name, logs)

    def eval_function(self, _cmd: Function):
        """ Evaluate a function type BrokerCMD """
        fn = getattr(update_tasks, _cmd.f_name)
        return fn(**_cmd.args)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = BrokerCMD.from_bytes(message.body)

            if br.executor != ExecutorsType.function:
                # console.print("Update consumer cannot evaluate non function type packets !!!", style="bold red")
                raise ValueError()
            try:
                result = self.eval_function(br)
            except exc.ZerospeechException:
                out.Console.Logger.error(f"Command {br} returned non 0 code")
            else:
                # eval success
                # 1. report back ?
                out.Console.info(result)
