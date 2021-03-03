import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path

from pydantic import AnyHttpUrl, ValidationError
from rich.console import Console
from rich.table import Table
from rich import inspect

from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import challenges as ch_queries

# Pretty Printing
console = Console()


class ChallengesCMD(CommandCollection):

    @property
    def description(self) -> str:
        return 'command group to administrate challenges'

    @property
    def name(self) -> str:
        return 'challenges'


class ListChallenges(CMD):
    """ cmd to list all challenges"""

    def __init__(self, cmd_path):
        super(ListChallenges, self).__init__(cmd_path)

        # custom arguments
        self.parser.add_argument('-a', '--include-all',
                                 dest='include_all', action='store_true',
                                 help='include non-active/expired challenges')

    @property
    def name(self) -> str:
        return 'list'

    @property
    def short_description(self):
        return 'list available challenges'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        loop = asyncio.get_event_loop()
        challenge_lst = loop.run_until_complete(
            ch_queries.list_challenges(include_all=args.include_all)
        )

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("label")
        table.add_column("active")
        table.add_column("url")
        table.add_column("back-end")
        table.add_column("start_date")
        table.add_column("end_date")

        for ch in challenge_lst:
            table.add_row(
                f"{ch.id}", f"{ch.label}", f"{ch.active}", f"{ch.url}",
                f"{ch.backend}", f"{ch.start_date.strftime('%d/%m/%Y')}"
            )
        # print
        console.print(table)


class AddChallenge(CMD):
    """ Command to create new challenges """

    def __init__(self, cmd_path):
        super(AddChallenge, self).__init__(cmd_path)

        self.parser.add_argument('--dry-run',
                                 dest='dry_run', action='store_true',
                                 help='does not insert into database')

        self.parser.add_argument('-f', '--from-file', dest='from_file',
                                 help='Load challenges from a json file')

    @property
    def name(self) -> str:
        return 'new'

    @property
    def short_description(self):
        return 'create a new challenge'

    def run(self, argv):
        args = self.parser.parse_args(argv)
        try:
            if args.from_file:
                file_path = Path(args.from_file)
                if not (file_path.is_file() and file_path.suffix == '.json'):
                    raise ValueError(f"Input file needs to exist and be a Valid JSON file.")
                obj = json.load(file_path.open())
                obj_list = [ch_queries.NewChallenge(**item) for item in obj]

            else:
                print("Creating a new Challenge")
                label = console.input("label: ")
                url = console.input("URL: ")
                start_date = console.input("start date (dd/mm/yyyy): ")
                end_date = console.input("end date (dd/mm/yyyy or none): ")
                print("\n")

                if end_date == "none":
                    end_date = None
                else:
                    end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

                obj = ch_queries.NewChallenge(
                    label=label,
                    active=False,
                    url=url,
                    backend="",
                    start_date=datetime.strptime(start_date, '%d/%m/%Y').date(),
                    end_date=end_date,
                )
                obj_list = [obj]

            if not args.dry_run:
                loop = asyncio.get_event_loop()
                for item in obj_list:
                    loop.run_until_complete(ch_queries.create_new_challenge(item))
                    console.print(f"insertion of {item.label} was successful:white_check_mark:")
            else:
                inspect(obj_list)

        except json.JSONDecodeError as e:
            console.print(f"json: {e} :x:")
        except ValidationError as e:
            console.print(f"{e} :x:")
        except ValueError as e:
            console.print(f"{e} :x:")


def get() -> ChallengesCMD:
    challenges = ChallengesCMD()

    challenges.add_cmd(ListChallenges(challenges.name))
    challenges.add_cmd(AddChallenge(challenges.name))

    return challenges
