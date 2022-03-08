import aio_pika

from zerospeech import out
from zerospeech.db.models.tasks import SubmissionUpdateMessage, UpdateType, message_from_bytes
from zerospeech.lib import submissions_lib
from .abstract_worker import AbstractWorker, ServerState


class UpdateTaskWorker(AbstractWorker):

    def __init__(self, *, config, server_state: ServerState):
        super(UpdateTaskWorker, self).__init__(config=config, server_state=server_state)

    def start_process(self, _id, submission_id: str):
        self.server_state.processes[_id] = submission_id
        with submissions_lib.SubmissionLogger(submission_id) as lg:
            lg.log(f"Updating submission <{_id}>")
            lg.log(f"<!-----------------------------------", append=True)

    def end_process(self, _id):
        submission_id = self.server_state.processes.get(_id)
        del self.server_state.processes[_id]
        with submissions_lib.SubmissionLogger(submission_id) as lg:
            lg.log(f"Submission update {_id} completed!!")
            lg.log(f"----------------------------------/>", append=True)

    @staticmethod
    async def eval_function(msg: SubmissionUpdateMessage):
        """ Evaluate a function type BrokerCMD """
        with submissions_lib.SubmissionLogger(msg.submission_id) as lg:
            out.log.debug(msg.dict())

            if msg.updateType == UpdateType.evaluation_complete:
                await submissions_lib.complete_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == UpdateType.evaluation_failed:
                await submissions_lib.fail_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == UpdateType.evaluation_canceled:
                await submissions_lib.cancel_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            else:
                raise ValueError("Unknown update task !!!")

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = message_from_bytes(message.body)

            if not isinstance(br, SubmissionUpdateMessage):
                raise ValueError("Cannot process non SubmissionUpdateMessages")

            out.log.info(f"Received update request for {br.submission_id}")

            self.start_process(br.job_id, br.submission_id)
            await self.eval_function(br)
            self.end_process(br.job_id)
