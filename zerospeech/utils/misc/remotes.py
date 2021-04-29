import shutil
import subprocess
from typing import List

import yaml

from zerospeech import get_settings
from zerospeech.admin.model import NewEvaluatorItem

_settings = get_settings()


def check_host(host):
    """ Checks if a remote host is reachable raises ConnectionError if not"""
    res = subprocess.run(
        [shutil.which('ssh'), "-q", f"{host}", "exit"]
    )
    if res.returncode != 0:
        raise ConnectionError(f'Host {host} was unreachable')


def ssh_exec(host, cmd: List[str]):
    result = subprocess.run(
        [shutil.which('ssh'), f"{host}", *cmd],
        capture_output=True
    )
    if result.returncode == 0:
        return result.returncode, result.stdout.decode()
    return result.returncode, result.stderr.decode()


def discover_evaluators(hostname: str, bin_location) -> List[NewEvaluatorItem]:
    code, res = ssh_exec(hostname, ['cat', f"{bin_location}/index.yml"])
    if code != 0:
        raise FileNotFoundError(f"Host {hostname} has not evaluators at this location: {bin_location}")

    eval_data = yaml.load(res, Loader=yaml.FullLoader)
    evaluators = eval_data.get('evaluators', {})
    return [NewEvaluatorItem(label=key, executor=item.get('executor'),
                             host=hostname,
                             script_path=item.get('script_path'),
                             base_arguments=";".join(item.get('base_arguments', [])))
            for key, item in evaluators.items()
            ]


