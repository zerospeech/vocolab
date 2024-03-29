from vocolab import get_settings

_settings = get_settings()


def build_broker_url(backend: str = "rabbitmq"):  # noqa: unused => future proofing
    """ Build url to connect to broker server"""
    user = _settings.task_queue_options.RPC_USERNAME
    password = _settings.task_queue_options.RPC_PASSWORD
    host = _settings.task_queue_options.RPC_HOST
    vhost = _settings.task_queue_options.RPC_VHOST
    port = _settings.task_queue_options.RPC_PORT
    if vhost:
        vhost = f"{vhost}"
    else:
        vhost = "/"

    auth = ""
    if user:
        auth = f"{user}"

        if password:
            auth += f":{password}"

        auth += "@"

    host = f"{host}"
    if port:
        host += f":{port}"

    return f"amqp://{auth}{host}/{vhost}"
