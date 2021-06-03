from typing import List

import yaml

from zerospeech.db import models
from zerospeech.lib import _fs


def discover_evaluators(hostname: str, bin_location) -> List[models.cli.NewEvaluatorItem]:
    code, res = _fs.commons.ssh_exec(hostname, ['cat', f"{bin_location}/index.yml"])
    if code != 0:
        raise FileNotFoundError(f"Host {hostname} has not evaluators at this location: {bin_location}")

    eval_data = yaml.load(res, Loader=yaml.FullLoader)
    evaluators = eval_data.get('evaluators', {})
    return [models.cli.NewEvaluatorItem(label=key, executor=item.get('executor'),
                                        host=hostname,
                                        script_path=item.get('script_path'),
                                        base_arguments=";".join(item.get('base_arguments', [])))
            for key, item in evaluators.items()
            ]
