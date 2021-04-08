import argparse
import asyncio

from rich.console import Console
import aio_pika

from zerospeech.task_manager.pika_utils import message_dispatch
from zerospeech.task_manager.model import BrokerCMD

console = Console()


async def echo_processor(message: aio_pika.IncomingMessage):
    async with message.process():
        br = BrokerCMD.from_bytes(message.body)
        console.print(br)
        await asyncio.sleep(1)


def run(channel_name):
    """ Run Echo Message Broker """
    # todo see if this can be parallelized with multiprocess
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
