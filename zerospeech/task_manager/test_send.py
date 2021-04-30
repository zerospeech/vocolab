import argparse
import asyncio

from zerospeech.task_manager import Messenger, publish_message

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('channel_name')
    parser.add_argument('message')
    args = parser.parse_args()

    v = Messenger(label="test-label", message=args.message)

    # publish message
    asyncio.run(publish_message(v, args.channel_name))
