from celery import Celery
from celery import current_app
from celery.bin import worker as celery_worker

from zerospeech.settings import get_settings
from zerospeech import workers

_settings = get_settings()
celery_app = None

celery_app = Celery(_settings.CELERY_APP,
             backend='rpc://',
             broker='pyamqp://guest@localhost//')


# Registering tasks
for w in workers.__all__:
    celery_app.tasks.register(w())


def worker_server(options):
    # todo check how to make server
    app = current_app._get_current_object()

    worker = celery_worker.worker(app=app)

    options = {
        'broker': 'amqp://guest:guest@localhost:5672//',
        'loglevel': 'INFO',
        'traceback': True,
    }

    worker.run(**options)
