wsgi_app = "{{wsgi_app}}"
# bind as unix:socket or ip:port
bind = '{{bind_point}}'
# backlog size (number of pending connections)
backlog = 2048
# Number of processes to create
workers = {{nb_workers}}
worker_class = "{{worker_class}}"
worker_connections = 1000
timeout = 30
keepalive = 2
# nuclear verbose debugging
spew = False
# detach from current terminal by forking process
daemon = False
# Environment variables to set for processes
raw_env = [
    'ZR_ENV_FILE={{zr_env_file}}',
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
