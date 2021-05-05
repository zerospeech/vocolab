import argparse
import asyncio
from importlib import import_module

import aio_pika
from rich.console import Console

from zerospeech import exc
from zerospeech.task_manager.model import BrokerCMD, Function, ExecutorsType
from zerospeech.task_manager.pika_utils import message_dispatch
from zerospeech.task_manager import bg_tasks

console = Console()


def verify_bin(bin_path):
    pass


def eval_function(_cmd: Function):
    """ Evaluate a function type BrokerCMD """
    fn = getattr(bg_tasks, _cmd.f_name)
    return fn(**_cmd.args)


async def eval_processor(message: aio_pika.IncomingMessage):
    async with message.process():
        br = BrokerCMD.from_bytes(message.body)

        if br.executor != ExecutorsType.function:
            console.print("Update consumer cannot evaluate non function type packets !!!", style="bold red")
            raise ValueError()
        try:
            result = eval_function(br)
        except exc.ZerospeechException:
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

