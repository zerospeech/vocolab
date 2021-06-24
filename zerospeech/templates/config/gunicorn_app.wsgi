import uvicorn.workers

# bind as unix:socket or ip:port
bind = 'unix:/run/gunicorn.sock'
# backlog size (number of pending connections)
backlog = 2048
# Number of processes to create
workers = 4
# Class to use for workers (should be uvicorn class ? )
worker_class = uvicorn.workers.UvicornWorker
worker_connections = 1000
timeout = 30
keepalive = 2
# nuclear verbose debugging
spew = False
# detach from current terminal by forking process
daemon = False
# Environment variables to set for processes
raw_env = [
    'DJANGO_SECRET_KEY=something',
    'SPAM=eggs',
]
# The path to a pid file to write (None: use system default).
pidfile = None
# A mask for file permissions written by Gunicorn
umask = 0
# Switch worker processes to run as this user (None: use system default).
user = None
# Switch worker process to run as this group (None: use system default).
group = None
# A directory to store temporary request data when requests are read.
tmp_upload_dir = None
# Logging
errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# rename proctitle to appear with specific name (None: use system default).
proc_name = None


# Called just after a worker has been forked.
def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


# Called just prior to forking the worker subprocess.
def pre_fork(server, worker):
    pass


# Called just prior to forking off a secondary
#   master process during things like config reloading.
def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
