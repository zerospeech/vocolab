import asyncio
import shlex
import sys
from pathlib import Path

from rich.prompt import Confirm
from rich.table import Table

from vocolab import get_settings, out
from vocolab.admin import cmd_lib
from vocolab.db.q import challenges as ch_queries
from vocolab.lib import evaluators_lib

_settings = get_settings()


class EvaluatorsCMD(cmd_lib.CMD):
    """ Container for evaluator functions manipulation """

    def __init__(self, root, name, cmd_path):
        super(EvaluatorsCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        evaluators = asyncio.run(ch_queries.get_evaluators())

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("label")
        table.add_column("host")
        table.add_column("executor")
        table.add_column("script_path")
        table.add_column("executor_arguments")

        for ev in evaluators:
            table.add_row(
                f"{ev.id}", f"{ev.label}", f"{ev.host}", f"{ev.executor}",
                f"{ev.script_path}", f"{ev.executor_arguments}"
            )

        # print
        out.cli.print(table)


class ListHostsEvaluatorsCMD(cmd_lib.CMD):
    """ Command to list all hosts containing evaluators """

    def __init__(self, root, name, cmd_path):
        super(ListHostsEvaluatorsCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("BIN Dir")
        table.add_column("CONNECT")

        for host in _settings.HOSTS:
            if host not in _settings.REMOTE_BIN:
                continue
            try:
                if host in ("localhost", "127.0.0.1", _settings.hostname):
                    status = "[blue]:house:[/blue]"
                else:
                    status = "[green]:heavy_check_mark:[/green]"
                    evaluators_lib.check_host(host)
            except ConnectionError:
                status = "[red]:x:[/red]"

            table.add_row(
                f"{host}", f"{_settings.REMOTE_BIN[host]}", status,
            )

        # print
        out.cli.print(table)


class DiscoverEvaluatorsCMD(cmd_lib.CMD):
    """ Command to list all challenges"""

    def __init__(self, root, name, cmd_path):
        super(DiscoverEvaluatorsCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('--local', action='store_true')
        self.parser.add_argument('host')

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.local and Path(args.host).is_dir():
            raise NotImplemented('import of local evaluators is not implemented yet !!')

        if args.host not in _settings.HOSTS:
            out.cli.print(":x: Error specified host was not found", style="red")
            sys.exit(1)

        remote_dir = _settings.REMOTE_BIN.get(args.host, None)
        if remote_dir is None:
            out.cli.print(":x: Error specified host does not have a known bin dir", style="red")
            sys.exit(2)

        evaluators = evaluators_lib.discover_evaluators(args.host, remote_dir)
        # show
        out.cli.print(f"Found evaluators : {[ev.label for ev in evaluators]}")
        response = Confirm.ask("Do want to import them into the database?")
        if response:
            asyncio.run(ch_queries.add_evaluator(lst_eval=evaluators))
            out.cli.print(":heavy_check_mark: successfully inserted evaluators")


class UpdateBaseArguments(cmd_lib.CMD):
    """Update base arguments of an evaluator """
    
    def __init__(self, root, name, cmd_path):
        super(UpdateBaseArguments, self).__init__(root, name, cmd_path)

        # arguments
        self.parser.add_argument("evaluator_id", type=int, help='The id of the entry')

    def run(self, argv):
        """ Update base arguments of an evaluator

            Pass a list of arguments to give to the evaluator
        """
        args, rest = self.parser.parse_known_args(argv)

        asyncio.run(
            ch_queries.edit_evaluator_args(eval_id=args.evaluator_id, arg_list=rest)
        )
        out.cli.info(":heavy_check_mark: successfully updated evaluator")
