import argparse
import asyncio
import subprocess
from pathlib import Path

from rich.console import Console
import aio_pika

from zerospeech import get_settings, exc
from zerospeech.task_manager.pika_utils import message_dispatch
from zerospeech.task_manager.model import BrokerCMD, SubProcess

_settings = get_settings()
console = Console()


def verify_bin(bin_path):
    """ Verifies that bin_path is in the registered bin folder of the current host """
    my_bin = _settings.REMOTE_BIN.get(_settings.hostname, None)
    if my_bin not in [bin_path, *bin_path.parents]:
        raise exc.SecurityError(f'attempting to execute a file not in authorized directory {bin_path}')


def eval_subprocess(_cmd: SubProcess):
    """ Evaluate a subprocess type BrokerCMD """
    bin_path = Path(_cmd.exe_path)
    verify_bin(bin_path)
    script = bin_path / _cmd.p_name
    result = subprocess.run(
        [_cmd.executor.to_exec(), str(script), *_cmd.args], capture_output=True, text=True
    )
    # process results
    if result.returncode != 0:
        return result.returncode, result.stderr
    return result.returncode, result.stdout


async def eval_processor(message: aio_pika.IncomingMessage):
    async with message.process():
        br = BrokerCMD.from_bytes(message.body)

        if not br.executor.is_subprocess:
            console.print("Eval consumer cannot evaluate non subprocess packet!!!", style="bold red")

        status, result = eval_subprocess(br)
        # todo create failed_stuff logfile
        if status != 0:
            print(f"Command {br} returned non 0 code")

        else:
            # eval success
            # 1. report back ?
            print(result)


def run(channel_name):
    """ Run Echo Message Broker """
    # todo see if this can be parallelized with multiprocess
    main_loop = asyncio.get_event_loop()
    connection = main_loop.run_until_complete(
        message_dispatch(main_loop, channel_name, eval_processor)
    )
    try:
        main_loop.run_forever()
    finally:
        main_loop.run_until_complete(connection.close())


def cmd():
    # run demo server
    parser = argparse.ArgumentParser()
    parser.add_argument('channel_name')
    args = parser.parse_args()
    run(args.channel_name)


if __name__ == '__main__':
    cmd()

