import asyncio
import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError, parse_obj_as, AnyHttpUrl
from rich.table import Table

from vocolab import out
from vocolab.core import cmd_lib
from vocolab.data import models, model_queries


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
        challenge_lst: model_queries.ChallengeList = loop.run_until_complete(
            model_queries.ChallengeList.get(include_all=args.include_all)
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

        for ch in challenge_lst.items:
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
        out.cli.print(table)


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
                out.cli.print("Creating a new Challenge", style="bold purple")
                label = out.cli.raw.input("[bold]label:[/bold] ")
                url = out.cli.raw.input("[bold]URL:[/bold] ")
                start_date = out.cli.raw.input("[bold]start date (dd/mm/yyyy):[/bold] ")
                end_date = out.cli.raw.input("[bold]end date (dd/mm/yyyy or none):[/bold] ")
                out.cli.print("\n")

                if end_date == "none":
                    end_date = None
                else:
                    end_date = datetime.strptime(end_date, '%d/%m/%Y').date()

                obj = models.cli.NewChallenge(
                    label=label,
                    active=False,
                    url=parse_obj_as(AnyHttpUrl, url),
                    evaluator=None,
                    start_date=datetime.strptime(start_date, '%d/%m/%Y').date(),
                    end_date=end_date,
                )
                obj_list = [obj]

            if not args.dry_run:
                for item in obj_list:
                    asyncio.run(model_queries.Challenge.create(item))
                    out.cli.print(f"insertion of {item.label} was successful:white_check_mark:",
                                  style="bold green")
            else:
                out.cli.inspect(obj_list)

        except json.JSONDecodeError as e:
            out.cli.error(f":x:\tjson: {e}")
        except ValidationError as e:
            out.cli.error(f":x:\t{e}")
        except ValueError as e:
            out.cli.error(f":x:\t{e}")


class SetChallenge(cmd_lib.CMD):
    """ Command to alter properties of Challenges"""

    def __init__(self, root, name, cmd_path):
        super(SetChallenge, self).__init__(root, name, cmd_path)
        self.challenge_fields = model_queries.Challenge.get_field_names()
        self.challenge_fields.remove('id')

        # arguments
        self.parser.add_argument('id', help='ID of the challenge to update')
        self.parser.add_argument('field_name', type=str, choices=self.challenge_fields,
                                 help='The name of the field')
        self.parser.add_argument('value', help='The new value of the field')

    @staticmethod
    async def update_property(challenge_id: int, field_name: str, value: str):
        ch = await model_queries.Challenge.get(challenge_id=challenge_id)
        return await ch.update_property(
            variable_name=field_name,
            value=value,
            allow_parsing=True
        )

    def run(self, argv):
        args = self.parser.parse_args(argv)
        res = asyncio.run(
            self.update_property(args.id, args.field_name, args.value)
        )
        out.cli.info(f"Field {args.field_name}={res} :white_check_mark:")
