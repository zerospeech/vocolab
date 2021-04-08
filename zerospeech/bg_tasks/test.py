import asyncio

from rich.console import Console

from zerospeech.task_manager import pika_utils, model

console = Console()


if __name__ == '__main__':
    msg = model.Messenger(
        label="testing-async-messaging",
        message="Hello there"
    )
    console.print("=>", msg)
    asyncio.run(pika_utils.publish_message(msg, "zr_test"))
