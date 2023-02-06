import asyncio
import string
import sys
from pathlib import Path

from pydantic import EmailStr

from vocolab import get_settings, out
from vocolab.core import notify, cmd_lib

_settings = get_settings()


class TestCMD(cmd_lib.CMD):
    """ Administrate Task Workers """

    def __init__(self, root, name, cmd_path):
        super(TestCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()
        sys.exit(0)


class TestEmail(cmd_lib.CMD):
    """ Send email to test SMTP Parameters """

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


class TestDebugCMD(cmd_lib.CMD):
    """ Test things as cmd """

    def __init__(self, root, name, cmd_path):
        super(TestDebugCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        out.cli.info("Nothing to see here move along")
