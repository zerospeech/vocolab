""" RabbitMQ Echo consumer worker
A simple worker that reads messages from a channel in the queue.
"""
import argparse
import asyncio

import aio_pika
from rich.console import Console

from zerospeech.task_manager.model import BrokerCMD, ExecutorsType, Messenger
from zerospeech.task_manager.pika_utils import message_dispatch

console = Console()


def eval_message(cmd: Messenger):
    """ Evaluate a message type BrokerCMD """
    # todo: maybe should add logging
    return cmd.message


async def echo_processor(message: aio_pika.IncomingMessage):
    async with message.process():
        br = BrokerCMD.from_bytes(message.body)
        if br.executor != ExecutorsType.messenger:
            console.print("Echo Consumer cannot handle non message type packets !!", style="bold red")
        else:
            msg = eval_message(br)
            console.print(msg)


def run(channel_name):
    """ Run Echo Message Broker """
    main_loop = asyncio.get_event_loop()
    connection = main_loop.run_until_complete(
        message_dispatch(main_loop, channel_name, echo_processor)
    )
    try:
        main_loop.run_forever()
    finally:
        main_loop.run_until_complete(connection.close())


if __name__ == '__main__':
    # run demo server
    parser = argparse.ArgumentParser()
    parser.add_argument('channel_name')
    args = parser.parse_args()
    run(args.channel_name)
