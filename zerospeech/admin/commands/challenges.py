import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError
from rich.table import Table

from zerospeech import out
from zerospeech.admin import cmd_lib
from zerospeech.db.q import challengesQ
from zerospeech.db import schema, models


class ChallengesCMD(cmd_lib.CMD):
    """ Command for challenge administration (default: list)"""

    def __init__(self, root, name, cmd_path):
        super(ChallengesCMD, self).__init__(root, name, cmd_path)

        # custom arguments
        self.parser.add_argument('-a', '--include-all',
                                 dest='include_all', action='store_true',
                                 help='include non-active/expired challenges')

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        loop = asyncio.get_event_loop()
        challenge_lst = loop.run_until_complete(
            challengesQ.list_challenges(include_all=args.include_all)
        )

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("label")
        table.add_column("active")
        table.add_column("url")
        table.add_column("start_date")
        table.add_column("end_date")
        table.add_column("evaluator")

        for ch in challenge_lst:
            if ch.end_date:
                end_date_str = ch.end_date.strftime('%d/%m/%Y')
            else:
                end_date_str = None

            table.add_row(
                f"{ch.id}", f"{ch.label}", f"{ch.active}", f"{ch.url}",
                f"{ch.start_date.strftime('%d/%m/%Y')}",
                f"{end_date_str}", f"{ch.evaluator}"
            )
        # print
        out.Console.print(table)


class AddChallengeCMD(cmd_lib.CMD):
    """ Command to create new challenges """

    def __init__(self, root, name, cmd_path):
        super(AddChallengeCMD, self).__init__(root, name, cmd_path)

        self.parser.add_argument('--dry-run',
                                 dest='dry_run', action='store_true',
                                 help='does not insert into database')

        self.parser.add_argument('-f', '--from-file', dest='from_file',
                                 help='Load challenges from a json file')

    def run(self, argv):
        args = self.parser.parse_args(argv)
        try:
            if args.from_file:
                file_path = Path(args.from_file)
                if not (file_path.is_file() and file_path.suffix == '.json'):
                    raise ValueError(f"Input file needs to exist and be a Valid JSON file.")
                obj = json.load(file_path.open())
                obj_list = [models.cli.NewChallenge(**item) for item in obj]

            else:
                out.Console.print("Creating a new Challenge", style="bold purple")
                label = out.Console.console.input("[bold]label:[/bold] ")
                url = out.Console.console.input("[bold]URL:[/bold] ")
                start_date = out.Console.console.input("[bold]start date (dd/mm/yyyy):[/bold] ")
                end_date = out.Console.console.input("[bold]end date (dd/mm/yyyy or none):[/bold] ")
                print("\n")

                if end_date == "none":
                    end_date = None
                else:
                    end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

                obj = models.cli.NewChallenge(
                    label=label,
                    active=False,
                    url=url,
                    evaluator=None,
                    start_date=datetime.strptime(start_date, '%d/%m/%Y').date(),
                    end_date=end_date,
                )
                obj_list = [obj]

            if not args.dry_run:
                for item in obj_list:
                    asyncio.run(challengesQ.create_new_challenge(item))
                    out.Console.print(f"insertion of {item.label} was successful:white_check_mark:",
                                      style="bold green")
            else:
                out.Console.inspect(obj_list)

        except json.JSONDecodeError as e:
            out.Console.error(f":x:\tjson: {e}")
        except ValidationError as e:
            out.Console.error(f":x:\t{e}")
        except ValueError as e:
            out.Console.error(f":x:\t{e}")


class SetChallenge(cmd_lib.CMD):
    """ Command to alter properties of Challenges"""

    def __init__(self, root, name, cmd_path):
        super(SetChallenge, self).__init__(root, name, cmd_path)
        # arguments
        self.parser.add_argument('id', help='ID of the challenge to update')
        self.parser.add_argument('field', help='the field that will be updated')
        self.parser.add_argument('value', help='the value to add')
        self.challenge_fields = schema.Challenge.__annotations__
        del self.challenge_fields['id']

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
            out.Console.print(f":x: field : {args.field} is not a valid field!", style="bold red")
            out.Console.print(f":right_arrow: please use one of the following fields : "
                              f"{list(self.challenge_fields.keys())}",
                              style="bold green")
            sys.exit(1)

        type_safe_value = self._type_safety(args.field, args.value)
        asyncio.run(
            challengesQ.set_challenge_property(
                ch_id=args.id, property_name=args.field, value=type_safe_value
            )
        )
        out.Console.print(f"challenge:white_check_mark:",
                          style="bold green")
