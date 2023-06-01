import asyncio
import json
import sys
from pathlib import Path

from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

from vocolab import out
from vocolab.core import leaderboards_lib, cmd_lib
from vocolab.data import model_queries


class LeaderboardCMD(cmd_lib.CMD):
    """ Administrate Leaderboard entries (default: list)"""

    def __init__(self, root, name, cmd_path):
        super(LeaderboardCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        try:
            leaderboards: model_queries.LeaderboardList = asyncio.run(model_queries.LeaderboardList.get_all())
        except ValueError:
            leaderboards = model_queries.LeaderboardList(items=[])

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column('Label')
        table.add_column('Archived')
        table.add_column('Static Files')
        table.add_column('Benchmark ID')
        table.add_column('Key', no_wrap=False, overflow='fold')
        for entry in leaderboards:
            table.add_row(
                f"{entry.label}", f"{entry.archived}",
                f"{entry.static_files}", f"{entry.benchmark_id}",
                f"{entry.sorting_key}"
            )
        out.cli.print(table, no_wrap=False)


class CreateLeaderboardCMD(cmd_lib.CMD):
    """ Create a new leaderboard entry """

    def __init__(self, root, name, cmd_path):
        super(CreateLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-f', '--from-file', type=str, help="Load leaderboards from a json file")

    @staticmethod
    def ask_input():
        label = Prompt.ask("Label: ")
        benchmark_id = IntPrompt.ask("Benchmark ID")
        add_static_files = Confirm.ask("Does this leaderboard include static files", default=True)
        archived = not Confirm.ask("Does this leaderboard accept new entries", default=True)

        return dict(
            label=label,
            benchmark_id=benchmark_id,
            archived=archived,
            static_files=add_static_files,
            sorting_key=None
        )

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.from_file:
            input_file = Path(args.from_file)
            if not input_file.is_file():
                out.cli.error(f"File given ({input_file}) does not exist")
                sys.exit(1)

            if input_file.suffix != ".json":
                out.cli.error(f"File given ({input_file}) does not appear to be a json file")
                sys.exit(1)

            with input_file.open() as fp:
                lds = json.load(fp)

        else:
            lds = [self.ask_input()]

        for item in lds:
            asyncio.run(model_queries.Leaderboard.create(
                model_queries.Leaderboard(
                    label=item.get("label"),
                    benchmark_id=item.get("benchmark_id"),
                    static_files=item.get("static_files", False),
                    archived=item.get("archived", False),
                    sorting_key=item.get("sorting_key", None),
                )
            ))
            out.cli.info(f"Successfully created leaderboard : {item.get('label')}")


class EditLeaderboardCMD(cmd_lib.CMD):
    """ Edit Leaderboard entries """

    def __init__(self, root, name, cmd_path):
        super(EditLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.leaderboard_fields = model_queries.Leaderboard.get_field_names()

        # arguments
        self.parser.add_argument("leaderboard_id", type=str, help='The id of the entry')
        self.parser.add_argument("field_name", type=str, choices=self.leaderboard_fields,
                                 help="The name of the field")
        self.parser.add_argument('field_value', help="The new value of the field")

    @staticmethod
    async def update_value(leaderboard_id: str, field_name: str, value: str):
        leaderboard = await model_queries.Leaderboard.get(leaderboard_id=leaderboard_id)
        return await leaderboard.update_property(variable_name=field_name, value=value, allow_parsing=True)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        res = asyncio.run(self.update_value(
            leaderboard_id=args.leaderboard_id,
            field_name=args.field_name,
            value=args.field_value
        ))
        out.cli.info(f"Field {args.field_name}={res} :white_check_mark:")


class ShowLeaderboardCMD(cmd_lib.CMD):
    """ Print final leaderboard object """

    def __init__(self, root, name, cmd_path):
        super(ShowLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('label', type=str)
        self.parser.add_argument('--raw-output', action="store_true",
                                 help="Print in raw json without formatting")

    @staticmethod
    async def get_leaderboard(label: str):
        return await model_queries.Leaderboard.get(label)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        ld = asyncio.run(self.get_leaderboard(label=args.label))
        leaderboard_obj = ld.get_dir().load_object(from_cache=True, raw=True)

        if args.raw_output:
            out.cli.raw.out(json.dumps(leaderboard_obj, indent=4))
        else:
            out.cli.print(leaderboard_obj)


class BuildLeaderboardCMD(cmd_lib.CMD):
    """ Compile entries into the leaderboard """

    def __init__(self, root, name, cmd_path):
        super(BuildLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('leaderboard_id', type=int, help='The id of the leaderboard')

    @staticmethod
    async def get_leaderboard(label: str):
        return await model_queries.Leaderboard.get(label)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        ld = asyncio.run(self.get_leaderboard(label=args.label))
        ld.get_dir().mkcache()
        out.cli.info(f"Successfully build {ld}")


class LeaderboardEntries(cmd_lib.CMD):
    """ Leaderboard entries """

    def __init__(self, root, name, cmd_path):
        super(LeaderboardEntries, self).__init__(root, name, cmd_path)
        self.parser.add_argument('--by-leaderboard', type="str")
        self.parser.add_argument('--by-model', type="str")
        self.parser.add_argument('--by-benchmark', type="str")


class ImportLeaderboardEntries(cmd_lib.CMD):
    """ Compile entries into the leaderboard """

    def __init__(self, root, name, cmd_path):
        super(BuildLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('leaderboard_id', type=int, help='The id of the leaderboard')

    @staticmethod
    async def get_leaderboard(label: str):
        return await model_queries.Leaderboard.get(label)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        ld = asyncio.run(self.get_leaderboard(label=args.label))
        ld.get_dir().mkcache()
        out.cli.info(f"Successfully build {ld}")
