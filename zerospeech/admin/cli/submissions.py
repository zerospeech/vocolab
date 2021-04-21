import asyncio
import json
import sys
from datetime import datetime, date
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from rich import inspect

from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import challenges as ch_queries
from zerospeech.db.schema import challenges as db_challenges
from zerospeech.utils import misc

# Pretty Printing
console = Console()


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
        self.parser.add_argument('-s', '--status',
                                 choices=[el.value for el in db_challenges.SubmissionStatus],
                                 help='Filter by status')

    @property
    def name(self) -> str:
        return 'list'

    def run(self, argv):
        args = self.parser.parse_args(argv)
        items = asyncio.run(ch_queries.list_submission(args.user, args.status))

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
                                 choices=[el.value for el in db_challenges.SubmissionStatus]
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


def get() -> SubmissionCMD:
    submission = SubmissionCMD()
    submission.add_cmd(ListSubmissions(submission.name))
    submission.add_cmd(SetSubmission(submission.name))

    return submission
