import sys

from vocolab import out, get_settings
from vocolab.core import cmd_lib

# api settings
from vocolab.data.models.tasks import SimpleLogMessage, SubmissionUpdateMessage, UpdateType
from vocolab.worker import server as message_server

_settings = get_settings()


class MessagingCMD(cmd_lib.CMD):
    """ Custom Message Command"""
    
    def __init__(self, root, name, cmd_path):
        super(MessagingCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        self.parser.print_help()


class UpdateMessageCMD(cmd_lib.CMD):
    """ Send an update message """

    def __init__(self, root, name, cmd_path):
        super(UpdateMessageCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('submission_id')
        self.parser.add_argument('update_type', choices=[t.value for t in UpdateType]) # noqa: enum has value attribute

    def run(self, argv):
        args = self.parser.parse_args(argv)
        submission_id = args.submission_id
        try:
            update_type = UpdateType(args.update_type)
        except KeyError:
            update_type = UpdateType.evaluation_undefined

        sum_ = SubmissionUpdateMessage(
            label=f"{_settings.app_options.hostname}-completed-{submission_id}",
            submission_id=submission_id,
            updateType=update_type,
            hostname=f"{_settings.app_options.hostname}"
        )

        # send update to channel
        message_server.update.delay(sum_=sum_.dict())


class EchoMessageCMD(cmd_lib.CMD):
    """ Send an echo message """

    def __init__(self, root, name, cmd_path):
        super(EchoMessageCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('message', type=str, nargs="+")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        slm = SimpleLogMessage(
            label="CLI-MSG-Testing",
            message=args.message,
        )
        # send message
        message_server.echo.delay(slm=slm)


class EvalMessageCMD(cmd_lib.CMD):
    """ Send an eval message """

    def __init__(self, root, name, cmd_path):
        super(EvalMessageCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        out.cli.info("Not Implemented !!!!")
        sys.exit(1)
