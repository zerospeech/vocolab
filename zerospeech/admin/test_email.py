import argparse
import asyncio
from pathlib import Path

from zerospeech.lib import notify


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("subject")
    parser.add_argument("-b" "--body-file", dest="body_file")
    args = parser.parse_args()

    if args.body_file:
        with Path(args.body_file).open() as fp:
            body = fp.read()
    else:
        body = ""

    # send email
    asyncio.run(notify.email.simple_html_email(
        emails=[args.email],
        subject=args.subject,
        content=body
    ))
