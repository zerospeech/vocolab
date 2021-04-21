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


class ChallengesCMD(CommandCollection):
    __cmd_list__ = {}

    @property
    def description(self) -> str:
        return 'command group to administrate challenges'

    @property
    def name(self) -> str:
        return 'challenges'


class ListChallenges(CMD):
    """ Command to list all challenges"""

    def __init__(self, cmd_path):
        super(ListChallenges, self).__init__(cmd_path)

        # custom arguments
        self.parser.add_argument('-a', '--include-all',
                                 dest='include_all', action='store_true',
                                 help='include non-active/expired challenges')

    @property
    def name(self) -> str:
        return 'list'

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
            if ch.end_date:
                end_date_str = ch.end_date.strftime('%d/%m/%Y')
            else:
                end_date_str = None

            table.add_row(
                f"{ch.id}", f"{ch.label}", f"{ch.active}", f"{ch.url}",
                f"{ch.backend}", f"{ch.start_date.strftime('%d/%m/%Y')}",
                f"{end_date_str}"
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
                console.print("Creating a new Challenge", style="bold purple")
                label = console.input("[bold]label:[/bold] ")
                url = console.input("[bold]URL:[/bold] ")
                start_date = console.input("[bold]start date (dd/mm/yyyy):[/bold] ")
                end_date = console.input("[bold]end date (dd/mm/yyyy or none):[/bold] ")
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
                with misc.get_event_loop() as loop:
                    for item in obj_list:
                        loop.run_until_complete(ch_queries.create_new_challenge(item))
                        console.print(f"insertion of {item.label} was successful:white_check_mark:",
                                      style="bold green")
            else:
                inspect(obj_list)

        except json.JSONDecodeError as e:
            console.print(f":x:\tjson: {e}", style="bold red")
        except ValidationError as e:
            console.print(f":x:\t{e}", style="bold red")
        except ValueError as e:
            console.print(f":x:\t{e}", style="bold red")


class SetChallenge(CMD):
    """ Command to alter properties of Challenges"""

    def __init__(self, cmd_path):
        super(SetChallenge, self).__init__(cmd_path)
        # arguments
        self.parser.add_argument('id', help='ID of the challenge to update')
        self.parser.add_argument('field', help='the field that will be updated')
        self.parser.add_argument('value', help='the value to add')
        self.challenge_fields = db_challenges.Challenge.__annotations__
        del self.challenge_fields['id']

    @property
    def name(self) -> str:
        return 'set'

    def _type_safety(self, field_name: str, value: str):
        print(field_name)
        if field_name in ('start_date', 'end_date'):
            return datetime.strptime(value, "%d/%m/%Y").date()
        else:
            p_type = self.challenge_fields[field_name]
            return p_type(value)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.field not in self.challenge_fields.keys():
            console.print(f":x: field : {args.field} is not a valid field!", style="bold red")
            console.print(f":right_arrow: please use one of the following fields : "
                          f"{list(self.challenge_fields.keys())}",
                          style="bold green")
            sys.exit(1)

        type_safe_value = self._type_safety(args.field, args.value)
        asyncio.run(
            ch_queries.set_challenge_property(
                args.id, args.field, type_safe_value
            )
        )
        console.print(f"challenge:white_check_mark:",
                      style="bold green")


def get() -> ChallengesCMD:
    challenges = ChallengesCMD()
    challenges.add_cmd(ListChallenges(challenges.name))
    challenges.add_cmd(AddChallenge(challenges.name))
    challenges.add_cmd(SetChallenge(challenges.name))

    return challenges
