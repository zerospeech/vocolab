import asyncio
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.api.models import NewSubmissionRequest
from zerospeech.db.q import challenges as ch_queries, users as usr_queries
from zerospeech.db.schema import challenges as db_challenges
# Pretty Printing
from zerospeech.utils import submissions as sub_utils, misc

console = Console()
error_console = Console(stderr=True, style="bold red")
success_console = Console(style="bold green")


class SubmissionCMD(CommandCollection):
    __cmd_list__ = {}

    @property
    def description(self) -> str:
        return 'command group to administrate submissions'

    @property
    def name(self) -> str:
        return 'submissions'


class ListSubmissions(CMD):
    """ List submissions """

    def __init__(self, cmd_path):
        super(ListSubmissions, self).__init__(cmd_path)

        # custom arguments
        self.parser.add_argument('-u', '--user', type=int, help='Filter by user ID')
        self.parser.add_argument('-t', '--track', type=int, help='Filter by track ID')
        self.parser.add_argument('-s', '--status',
                                 choices=[el.value for el in db_challenges.SubmissionStatus],
                                 help='Filter by status')

    @property
    def name(self) -> str:
        return 'list'

    def run(self, argv):
        args = self.parser.parse_args(argv)
        fn_args = {}

        if args.user:
            fn_args['by_user'] = args.user

        if args.track:
            fn_args['by_track'] = args.track

        if args.status:
            fn_args['by_status'] = args.status

        items = asyncio.run(ch_queries.list_submission(**fn_args))

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("User")
        table.add_column("Challenge")
        table.add_column("Date")
        table.add_column("Status")

        for i in items:
            table.add_row(
                f"{i.id}", f"{i.user_id}", f"{i.track_id}", f"{i.submit_date.strftime('%d/%m/%Y')}",
                f"{i.status}"
            )
        # print
        console.print(table)


class SetSubmission(CMD):
    """ Set submission status """

    def __init__(self, cmd_path):
        super(SetSubmission, self).__init__(cmd_path)

        # custom arguments
        self.parser.add_argument("submission_id")
        self.parser.add_argument('status',
                                 choices=[str(el.value) for el in db_challenges.SubmissionStatus]
                                 )

    @property
    def name(self) -> str:
        return 'set'

    def run(self, argv):
        args = self.parser.parse_args(argv)
        asyncio.run(ch_queries.update_submission_status(
            args.submission_id, args.status
        ))


class DeleteSubmission(CMD):
    """ Delete a submission """

    def __init__(self, cmd_path):
        super(DeleteSubmission, self).__init__(cmd_path)

        # custom arguments
        self.parser.add_argument("submission_id")

    @property
    def name(self) -> str:
        return 'set'

    def run(self, argv):
        args = self.parser.parse_args(argv)
        asyncio.run(ch_queries.update_submission_status(
            args.submission_id, args.status
        ))


class CreateSubmission(CMD):
    """ Adds a submission """

    def __init__(self, cmd_path):
        super(CreateSubmission, self).__init__(cmd_path)
        self.parser.add_argument("challenge_id", type=int)
        self.parser.add_argument("user_id", type=int)
        self.parser.add_argument("archive")

    @property
    def name(self) -> str:
        return "create"

    def run(self, argv):
        args = self.parser.parse_args(argv)
        archive = Path(args.archive)

        if not archive.is_file():
            error_console.print(f'Requested file {archive} does not exist')

        async def create_submission(ch_id, user_id):
            try:
                _challenge = await ch_queries.get_challenge(ch_id)
                _user = await usr_queries.get_user(by_uid=user_id)

                if not _user.enabled:
                    error_console.print(f'User {_user.username} is not allowed to perform this action')
                    sys.exit(1)

                _submission_id = await ch_queries.add_submission(ch_queries.NewSubmission(
                    user_id=_user.id,
                    track_id=_challenge.id
                ))
                return _challenge, _user, _submission_id
            except ValueError as e:
                error_console.print(e)
                sys.exit(1)

        # fetch db items
        challenge, user, submission_id = asyncio.run(create_submission(args.challenge_id, args.user_id))

        # create entry on disk
        sub_utils.make_submission_on_disk(
            submission_id, user.username, challenge.label,
            NewSubmissionRequest(
                filename=archive.name, hash=misc.md5sum(archive),
                multipart=False
            )
        )
        # fetch folder
        folder = sub_utils.get_submission_dir(submission_id)
        # copy file
        shutil.copy(archive, folder / 'archive.zip')
        misc.unzip(folder / 'archive.zip', folder / 'input')

        # set status
        (folder / 'upload.lock').unlink()
        asyncio.run(ch_queries.update_submission_status(submission_id, db_challenges.SubmissionStatus.uploaded))


class EvalSubmission(CMD):
    """ Launches the evaluation of a submission """
    sub_status = db_challenges.SubmissionStatus
    no_eval = {
        sub_status.uploading, sub_status.on_queue, sub_status.invalid,
        sub_status.uploading, sub_status.validating, sub_status.evaluating,
    }

    def __init__(self, cmd_path):
        super(EvalSubmission, self).__init__(cmd_path)
        # parameters
        self.parser.add_argument("submission_id")

    @property
    def name(self) -> str:
        return 'evaluate'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        submission: db_challenges.ChallengeSubmission = asyncio.run(ch_queries.get_submission(args.submission_id))

        if submission.status in self.no_eval:
            console.print(f"Cannot evaluate a submission that has status : {submission.status}")
            sys.exit(1)


def get() -> SubmissionCMD:
    submission = SubmissionCMD()
    submission.add_cmd(ListSubmissions(submission.name))
    submission.add_cmd(SetSubmission(submission.name))
    submission.add_cmd(EvalSubmission(submission.name))
    submission.add_cmd(CreateSubmission(submission.name))

    return submission
