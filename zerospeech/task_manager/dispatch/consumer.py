import asyncio
import aio_pika

from zerospeech.task_manager.model import queue_url


async def sample_process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        print(message.body)
        await asyncio.sleep(1)
        message.ack()


async def async_message_dispatch(loop, queue_name: str, process_fn):
    conn = await aio_pika.connect_robust(
       queue_url(), loop=loop
    )

    # Creating channel
    channel = await conn.channel()

    # Maximum message count which will be
    # processing at the same time.
    await channel.set_qos(prefetch_count=100)

    # Declaring queue
    queue = await channel.declare_queue(queue_name, auto_delete=True)

    await queue.consume(process_fn)

    return conn


if __name__ == "__main__":
    main_loop = asyncio.get_event_loop()
    connection = main_loop.run_until_complete(
        async_message_dispatch(main_loop, "zr_eval_queue", sample_process_message)
    )

    try:
        main_loop.run_forever()
    finally:
        main_loop.run_until_complete(connection.close())
