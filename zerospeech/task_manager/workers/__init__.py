from .echo_consumer import EchoWorker
from .update_consumer import UpdateTaskWorker
from .eval_consumer import EvalTaskWorker

WORKER_TYPE = {f"eval": EvalTaskWorker, "update": UpdateTaskWorker, "echo": EchoWorker}

