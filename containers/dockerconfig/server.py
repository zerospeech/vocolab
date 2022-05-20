import os


def from_env(key: str, default_value):
    if key in os.environ:
        return os.environ[key]
    else:
        return default_value


# Path to wsgi app object
wsgi_app = from_env('VC_WSGI_APP', "vocolab.api:app")
# server bind point
bind = from_env('VC_SERVER_BIND', "0.0.0.0:8000")
# backlog size (number of pending connections)
backlog = 2048
# Number of processes to create
workers = from_env('VC_GUNICORN_WORKERS', 4)
worker_class = from_env('VC_GUNICORN_WORKER_CLASS', "uvicorn.workers.UvicornWorker")
worker_connections = 1000
timeout = 30
keepalive = 2
# nuclear verbose debugging
spew = False
# detach from current terminal by forking process
daemon = False
# Environment variables to set for processes
raw_env = [
    'VOCO_ENV_FILE=/etc/vocolab/docker.env',
]
# The path to a pid file to write (None: use system default).
pidfile = None
# A mask for file permissions written by Gunicorn
umask = 0
# A directory to store temporary request data when requests are read.
tmp_upload_dir = None
# Logging
errorlog = None
loglevel = 'info'
accesslog = None
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# rename proctitle to appear with specific name (None: use system default).
proc_name = None
