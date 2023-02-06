import shlex
from typing import List

import yaml

from vocolab import get_settings
from vocolab.data import models
from vocolab.core import commons

_settings = get_settings()

# export
check_host = commons.check_host


def discover_evaluators(hostname: str, bin_location) -> List[models.cli.NewEvaluatorItem]:
    """ Connects to a host & builds a list of evaluators from the index.yml file """

    cmd = shlex.split(f'cat {bin_location}/index.yml')
    if hostname not in ('localhost', '127.0.0.1', _settings.app_options.hostname):
        code, res = commons.ssh_exec(hostname, cmd)
    else:
        code, res = commons.execute(cmd)

    if code != 0:
        raise FileNotFoundError(f"Host {hostname} has not evaluators at this location: {bin_location}")

    eval_data = yaml.load(res, Loader=yaml.FullLoader)
    evaluators = eval_data.get('evaluators', {})
    return [models.cli.NewEvaluatorItem(label=key, executor=item.get('executor'),
                                        host=hostname,
                                        script_path=item.get('script_path'),
                                        executor_arguments=shlex.join(item.get('executor_arguments', [])))
            for key, item in evaluators.items()
            ]