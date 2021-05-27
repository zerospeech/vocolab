import asyncio
import sys
from pathlib import Path

from rich.prompt import Confirm
from rich.table import Table

from zerospeech import get_settings, out
from zerospeech.admin import cmd_lib
from zerospeech.db.q import challenges as ch_queries
from zerospeech.utils import misc

_settings = get_settings()


class EvaluatorsCMD(cmd_lib.CMD):
    """ Container for evaluator functions manipulation """

    def __init__(self, root, name, cmd_path):
        super(EvaluatorsCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        self.parser.print_help()
        sys.exit(0)


class ListRegisteredEvaluatorsCMD(cmd_lib.CMD):
    """ Command to list all registered evaluators"""

    def __init__(self, root, name, cmd_path):
        super(ListRegisteredEvaluatorsCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        evaluators = asyncio.run(ch_queries.get_evaluators())

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("label")
        table.add_column("host")
        table.add_column("executor")
        table.add_column("script_path")
        table.add_column("base_arguments")

        for ev in evaluators:
            table.add_row(
                f"{ev.id}", f"{ev.label}", f"{ev.host}", f"{ev.executor}",
                f"{ev.script_path}", f"{ev.base_arguments.split(';')}"
            )

        # print
        out.Console.print(table)


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
                status = "[green]:heavy_check_mark:[/green]"
                misc.check_host(host)
            except ConnectionError:
                status = "[red]:x:[/red]"

            table.add_row(
                f"{host}", f"{_settings.REMOTE_BIN[host]}", status,
            )

        # print
        out.Console.print(table)


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
            out.Console.print(":x: Error specified host was not found", style="red")
            sys.exit(1)

        remote_dir = _settings.REMOTE_BIN.get(args.host, None)
        if remote_dir is None:
            out.Console.print(":x: Error specified host does not have a known bin dir", style="red")
            sys.exit(2)

        evaluators = misc.discover_evaluators(args.host, remote_dir)
        # show
        out.Console.print(f"Found evaluators : {[ev.label for ev in evaluators]}")
        response = Confirm.ask("Do want to import them into the database?")
        if response:
            asyncio.run(ch_queries.add_evaluator(lst_eval=evaluators))
            out.Console.print(":heavy_check_mark: successfully inserted evaluators")
