import asyncio
import shutil
import sys
from pathlib import Path

from rich.table import Table

from zerospeech import out
from zerospeech.admin import cmd_lib
from zerospeech.db.models.api import NewSubmissionRequest, NewSubmission
from zerospeech.db.q import challenges as ch_queries, users as usr_queries
from zerospeech.db.schema import challenges as db_challenges
from zerospeech.lib import submissions_lib


class SubmissionCMD(cmd_lib.CMD):
    """ List submissions """

    def __init__(self, root, name, cmd_path):
        super(SubmissionCMD, self).__init__(root, name, cmd_path)

        # custom arguments
        self.parser.add_argument('-u', '--user', type=int, help='Filter by user ID')
        self.parser.add_argument('-t', '--track', type=int, help='Filter by track ID')
        self.parser.add_argument('-s', '--status',
                                 choices=[el.value for el in db_challenges.SubmissionStatus],
                                 help='Filter by status')

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
        out.Console.print(table)


class SetSubmissionCMD(cmd_lib.CMD):
    """ Set submission status """

    def __init__(self, root, name, cmd_path):
        super(SetSubmissionCMD, self).__init__(root, name, cmd_path)

        # custom arguments
        self.parser.add_argument("submission_id")
        self.parser.add_argument('status',
                                 choices=[str(el.value) for el in db_challenges.SubmissionStatus]
                                 )

    def run(self, argv):
        args = self.parser.parse_args(argv)
        asyncio.run(ch_queries.update_submission_status(
            by_id=args.submission_id, status=args.status
        ))


class DeleteSubmissionCMD(cmd_lib.CMD):
    """ Delete a submission """

    def __init__(self, root, name, cmd_path):
        super(DeleteSubmissionCMD, self).__init__(root, name, cmd_path)

        # custom arguments
        self.parser.add_argument("submission_id")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        asyncio.run(ch_queries.drop_submission(
            by_id=args.submission_id,
        ))


class CreateSubmissionCMD(cmd_lib.CMD):
    """ Adds a submission """

    def __init__(self, root, name, cmd_path):
        super(CreateSubmissionCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("challenge_id", type=int)
        self.parser.add_argument("user_id", type=int)
        self.parser.add_argument("archive")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        archive = Path(args.archive)

        if not archive.is_file():
            out.Console.error(f'Requested file {archive} does not exist')

        async def create_submission(ch_id, user_id):
            try:
                _challenge = await ch_queries.get_challenge(challenge_id=ch_id)
                _user = await usr_queries.get_user(by_uid=user_id)

                if not _user.enabled:
                    out.Console.error(f'User {_user.username} is not allowed to perform this action')
                    sys.exit(1)

                _submission_id = await ch_queries.add_submission(new_submission=NewSubmission(
                    user_id=_user.id,
                    track_id=_challenge.id
                ))
                return _challenge, _user, _submission_id
            except ValueError:
                out.Console.exception()
                sys.exit(1)

        # fetch db items
        challenge, user, submission_id = asyncio.run(create_submission(args.challenge_id, args.user_id))

        # create entry on disk
        submissions_lib.make_submission_on_disk(
            submission_id, user.username, challenge.label,
            NewSubmissionRequest(
                filename=archive.name, hash=submissions_lib.md5sum(archive),
                multipart=False
            )
        )
        # fetch folder
        folder = submissions_lib.get_submission_dir(submission_id)
        # copy file
        shutil.copy(archive, folder / 'archive.zip')
        submissions_lib.unzip(folder / 'archive.zip', folder / 'input')

        # set status
        (folder / 'upload.lock').unlink()
        asyncio.run(
            ch_queries.update_submission_status(by_id=submission_id, status=db_challenges.SubmissionStatus.uploaded)
        )


class EvalSubmissionCMD(cmd_lib.CMD):
    """ Launches the evaluation of a submission """
    sub_status = db_challenges.SubmissionStatus
    no_eval = {
        sub_status.uploading, sub_status.on_queue, sub_status.invalid,
        sub_status.uploading, sub_status.validating, sub_status.evaluating,
    }

    def __init__(self, root, name, cmd_path):
        super(EvalSubmissionCMD, self).__init__(root, name, cmd_path)
        # parameters
        self.parser.add_argument("submission_id")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        submission: db_challenges.ChallengeSubmission = asyncio.run(ch_queries.get_submission(by_id=args.submission_id))

        if submission.status in self.no_eval:
            out.Console.print(f"Cannot evaluate a submission that has status : {submission.status}")
            sys.exit(1)
