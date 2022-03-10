from uuid import uuid4

from typing import Dict

from celery import Celery

from zerospeech import out, get_settings
from zerospeech.db.models import tasks
from zerospeech.lib import worker_lib

# """""""""""""""""""""""""""""""""""""
# todo: run a couple of evals to test
# todo: read up on what is the best pool/supervisor
# todo: estimate best concurrency number and thread vs process
# todo: [FINAL] merge in master branch
# """""""""""""""""""""""""""""""""""""
_settings = get_settings()
app = Celery(f"zr-worker-{str(uuid4())}")

app.conf.update({
    "broker_url": worker_lib.utils.build_broker_url(),
    'task_routes': {
        'echo-task': {'queue': _settings.QUEUE_CHANNELS['echo']},
        'update-task': {'queue': _settings.QUEUE_CHANNELS['update']},
        'eval-task': {'queue': _settings.QUEUE_CHANNELS['eval']}
    },
    'task_ignore_result': True
})


@app.task(name='echo-task', ignore_result=True)
def echo(slm: Dict):
    slm = tasks.SimpleLogMessage(**slm)
    worker_lib.tasks.echo_fn(slm)


@app.task(name='update-task', ignore_result=True)
def update(sum_: Dict):
    sum_ = tasks.SubmissionUpdateMessage(**sum_)
    out.log.log(f'updating {sum_.submission_id}')
    worker_lib.tasks.update_task_fn(sum_)


@app.task(name='eval-task', ignore_result=True)
def evaluate(sem: Dict):
    sem = tasks.SubmissionEvaluationMessage(**sem)
    out.log.log(f'evaluating {sem.submission_id}')
    worker_lib.tasks.evaluate_submission_fn(sem)
