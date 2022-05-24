import asyncio
import shutil
import sys
from pathlib import Path

from rich.table import Table

from vocolab import out, get_settings
from vocolab.admin import cmd_lib
from vocolab.db.models.api import NewSubmissionRequest, NewSubmission
from vocolab.db.q import challengesQ, userQ
from vocolab.db.schema import challenges as db_challenges
from vocolab.lib import submissions_lib


# api settings
_settings = get_settings()


class SubmissionCMD(cmd_lib.CMD):
    """ List submissions """

    def __init__(self, root, name, cmd_path):
        super(SubmissionCMD, self).__init__(root, name, cmd_path)

        # custom arguments
        self.parser.add_argument('-u', '--user', type=int, help='Filter by user ID')
        self.parser.add_argument('-t', '--track', type=int, help='Filter by track ID')
        self.parser.add_argument('-s', '--status',
                                 choices=db_challenges.SubmissionStatus.get_values(),
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

        items = asyncio.run(challengesQ.list_submission(**fn_args))

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("User")
        table.add_column("Challenge")
        table.add_column("Date")
        table.add_column("Status")
        table.add_column("Evaluator ID")
        table.add_column("Author Label")

        for i in items:
            table.add_row(
                f"{i.id}", f"{i.user_id}", f"{i.track_id}", f"{i.submit_date.strftime('%d/%m/%Y')}",
                f"{i.status}", f"{i.evaluator_id}", f"{i.author_label}"
            )
        # print
        out.cli.print(table)


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
        submission_fs = submissions_lib.get_submission_dir(args.submission_id, as_obj=True)
        submission_fs.clean_all_locks()
        asyncio.run(challengesQ.update_submission_status(
            by_id=args.submission_id, status=args.status
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
            out.cli.error(f'Requested file {archive} does not exist')

        async def create_submission(ch_id, user_id):
            try:
                _challenge = await challengesQ.get_challenge(challenge_id=ch_id)
                _user = await userQ.get_user(by_uid=user_id)

                if not _user.enabled:
                    out.cli.error(f'User {_user.username} is not allowed to perform this action')
                    sys.exit(1)

                _submission_id = await challengesQ.add_submission(new_submission=NewSubmission(
                    user_id=_user.id,
                    track_id=_challenge.id
                ), evaluator_id=_challenge.evaluator)
                return _challenge, _user, _submission_id
            except ValueError:
                out.cli.exception()
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
            challengesQ.update_submission_status(by_id=submission_id, status=db_challenges.SubmissionStatus.uploaded)
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
        self.parser.add_argument('-e', '--extra-args', action='store_true')

    def run(self, argv):
        args, extras = self.parser.parse_known_args(argv)

        if args.extra_args:
            extra_arguments = list(extras)
        else:
            extra_arguments = []

        submission: db_challenges.ChallengeSubmission = asyncio.run(challengesQ.get_submission(by_id=args.submission_id))

        if submission.status in self.no_eval:
            out.cli.print(f"Cannot evaluate a submission that has status : {submission.status}")
            sys.exit(1)

        asyncio.run(
            # todo check if status is correctly set.
            submissions_lib.evaluate(submission_id=submission.id, extra_args=extra_arguments)
        )


class FetchSubmissionFromRemote(cmd_lib.CMD):
    """ Fetch submission from a remote server (uses rsync) """

    def __init__(self, root, name, cmd_path):
        super(FetchSubmissionFromRemote, self).__init__(root, name, cmd_path)
        self.parser.add_argument("hostname")
        self.parser.add_argument("submission_id")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        if args.hostname not in list(_settings.REMOTE_STORAGE.keys()):
            out.cli.warning(f"Host {args.hostname} is not a valid remote storage host!\n")
            out.cli.warning(f"aborting transfer...")
            sys.exit(1)

        try:
            _ = asyncio.run(challengesQ.get_submission(by_id=args.submission_id))
        except ValueError:
            out.cli.warning(f"Submission id is not valid !!")
            out.cli.warning(f"aborting transfer...")
            sys.exit(1)

        # transferring
        submissions_lib.fetch_submission_from_remote(host=args.hostname, submission_id=args.submission_id)


class UploadSubmissionToRemote(cmd_lib.CMD):
    """ Upload a submission to a remote server (uses rsync) """

    def __init__(self, root, name, cmd_path):
        super(UploadSubmissionToRemote, self).__init__(root, name, cmd_path)
        self.parser.add_argument("hostname")
        self.parser.add_argument("submission_id")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.hostname not in list(_settings.REMOTE_STORAGE.keys()):
            out.cli.warning(f"Host {args.hostname} is not a valid remote storage host!\n")
            out.cli.warning(f"aborting transfer...")
            sys.exit(1)

        try:
            _ = asyncio.run(challengesQ.get_submission(by_id=args.submission_id))
        except ValueError:
            out.cli.warning(f"Submission id is not valid !!")
            out.cli.warning(f"aborting transfer...")
            sys.exit(1)

        # transferring
        submissions_lib.transfer_submission_to_remote(host=args.hostname, submission_id=args.submission_id)


class DeleteSubmissionCMD(cmd_lib.CMD):
    """ Deletes a submission """
    
    def __init__(self, root, name, cmd_path):
        super(DeleteSubmissionCMD, self).__init__(root, name, cmd_path)
        # parameters
        self.parser.add_argument("delete_by", choices=['by_id', 'by_user', 'by_track'],
                                 help="the id/status of the submission to delete")
        self.parser.add_argument('selector', help="Item to select submission by")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.delete_by == 'by_id':
            del_id = asyncio.run(submissions_lib.delete_submission(by_id=args.selector))
            submissions_lib.delete_submission_files(del_id[0])
            out.cli.info(f"Successfully deleted: {args.selector}")
        elif args.delete_by == 'by_user':
            deleted = asyncio.run(submissions_lib.delete_submission(by_user=int(args.selector)))

            for d in deleted:
                submissions_lib.delete_submission_files(d)
                out.cli.info(f"Successfully deleted: {d}")

        elif args.delete_by == 'by_track':
            deleted = asyncio.run(submissions_lib.delete_submission(by_track=int(args.selector)))

            for d in deleted:
                submissions_lib.delete_submission_files(d)
                out.cli.info(f"Successfully deleted: {d}")
        else:
            out.cli.error("Error type of deletion unknown")
            sys.exit(1)


class SubmissionSetEvaluator(cmd_lib.CMD):
    """ Update or set the evaluator of a submission"""
    
    def __init__(self, root, name, cmd_path):
        super(SubmissionSetEvaluator, self).__init__(root, name, cmd_path)
        self.parser.add_argument("submission_id", type=str)
        self.parser.add_argument("evaluator_id", type=int)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        asyncio.run(challengesQ.update_submission_evaluator(
            args.evaluator_id, by_id=args.submission_id
        ))


class SubmissionSetAuthorLabel(cmd_lib.CMD):
    """ Update or set the author_label of a submission """

    def __init__(self, root, name, cmd_path):
        super(SubmissionSetAuthorLabel, self).__init__(root, name, cmd_path)
        self.parser.add_argument("submission_id", type=str)
        self.parser.add_argument("author_label", type=str)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        asyncio.run(challengesQ.update_submission_author_label(
            args.author_label, by_id=args.submission_id
        ))


class ArchiveSubmissionCMD(cmd_lib.CMD):
    """ Archive submissions """

    def __init__(self, root, name, cmd_path):
        super(ArchiveSubmissionCMD, self).__init__(root, name, cmd_path)
        # parameters
        self.parser.add_argument("selector", help="the id/status of the submission to delete")
        self.parser.add_argument('-t', '--type', choices=['by_id', 'by_user', 'by_track'],
                                 help='deletion method', default='by_id')

    @staticmethod
    async def archive_submission(*args):
        for submission_id in args:
            # archive leaderboard entry
            await submissions_lib.archive_leaderboard_entries(submission_id)
            # remove submission from db
            await submissions_lib.delete_submission(by_id=submission_id)
            # zip & archive files
            submissions_lib.archive_submission_files(submission_id)

            out.cli.info(f"Successfully archived: {submission_id}")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.type == 'by_id':
            asyncio.run(self.archive_submission(args.selector))
        elif args.type == 'by_user':
            submissions = asyncio.run(challengesQ.list_submission(by_user=int(args.selector)))
            asyncio.run(self.archive_submission([sub.id for sub in submissions]))
        elif args.type == 'by_track':
            submissions = asyncio.run(challengesQ.list_submission(by_track=int(args.selector)))
            asyncio.run(self.archive_submission([sub.id for sub in submissions]))
        else:
            out.cli.error("Error type of deletion unknown")
            sys.exit(1)


