import aio_pika

from zerospeech import exc, out
from zerospeech.task_manager.model import SubmissionUpdateMessage, ExecutorsType
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker


class UpdateTaskWorker(AbstractWorker):

    def __init__(self, channel_name, logs, exe_module):
        super(UpdateTaskWorker, self).__init__(channel_name, logs)
        self.exe_module = exe_module

    def eval_function(self, _cmd: SubmissionUpdateMessage):
        """ Evaluate a function type BrokerCMD """
        fn = getattr(self.exe_module, _cmd.f_name)
        return fn(**_cmd.args)

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            # fixme replace broker
            br = ...  # BrokerCMD.from_bytes(message.body)

            if br.executor != ExecutorsType.function:
                out.Console.Logger.error('UpdateWorker: Cannot evaluate non function messages')
                raise ValueError(f"")
            try:
                result = self.eval_function(br)
            except exc.ZerospeechException:
                out.Console.Logger.error(f"{br.to_str()} -> returned non 0 code")
            else:
                out.Console.Logger.info(result)
