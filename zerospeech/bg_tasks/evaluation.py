from zerospeech.task_manager import BrokerCMD, ExecutorsType, QueuesNames
from zerospeech.task_manager import publish_message


async def send_eval_task(msg, loop=None):
    return await publish_message(msg, QueuesNames.eval_queue, loop)
