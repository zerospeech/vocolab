import asyncio
import sys
from pathlib import Path

from zerospeech import out, get_settings
from zerospeech.admin import cmd_lib
from zerospeech.db.models.tasks import SimpleLogMessage
from zerospeech.lib import notify
from zerospeech.lib.worker_lib.pika_utils import publish_message

_settings = get_settings()


class TestCMD(cmd_lib.CMD):
    """ Administrate Task Workers """

    def __init__(self, root, name, cmd_path):
        super(TestCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()
        sys.exit(0)


class TestEchoWorker(cmd_lib.CMD):
    """ Send a test message to the echo worker server """
    
    def __init__(self, root, name, cmd_path):
        super(TestEchoWorker, self).__init__(root, name, cmd_path)
        self.parser.add_argument("message", type=str)

    def run(self, argv):
        """ Send a test message to the echo worker server


        """
        args = self.parser.parse_args(argv)
        channel = _settings.QUEUE_CHANNELS.get('echo')
        msg = SimpleLogMessage(
            label="testing",
            message=f"{args.message}"
        )
        asyncio.run(publish_message(msg, channel))
        out.Console.info('Message delivered successfully !!')


class TestEmail(cmd_lib.CMD):
    """ Send an email to test SMTP Parameters """

    def __init__(self, root, name, cmd_path):
        super(TestEmail, self).__init__(root, name, cmd_path)
        self.parser.add_argument("email")
        self.parser.add_argument("subject")
        self.parser.add_argument("-b" "--body-file", dest="body_file")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        print(args)

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

