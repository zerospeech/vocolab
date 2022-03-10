from zerospeech import get_settings

_settings = get_settings()


def build_broker_url(backend: str = "rabbitmq"):  # noqa: unused => future proofing
    """ Build url to connect to broker server"""
    user = _settings.RPC_USERNAME
    password = _settings.RPC_PASSWORD
    host = _settings.RPC_HOST
    vhost = _settings.RPC_VHOST
    port = _settings.RPC_PORT
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
