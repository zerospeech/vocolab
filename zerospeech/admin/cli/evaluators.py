import asyncio
import sys

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from zerospeech import get_settings
from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import challenges as ch_queries
from zerospeech.utils import misc

_settings = get_settings()
# Pretty Printing
console = Console()


class EvaluatorsCMD(CommandCollection):
    """ Command to group actions on evaluator functions """
    __cmd_list__ = {}

    @property
    def name(self) -> str:
        return 'evaluator'


class ListRegisteredEvaluators(CMD):
    """ Command to list all registered evaluators"""

    @property
    def name(self) -> str:
        return 'list'

    def __init__(self, cmd_path):
        super(ListRegisteredEvaluators, self).__init__(cmd_path)

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
        console.print(table)


class ListHostsEvaluators(CMD):
    """ Command to list all hosts containing evaluators """

    @property
    def name(self) -> str:
        return 'hosts'

    def __init__(self, cmd_path):
        super(ListHostsEvaluators, self).__init__(cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("BIN Dir")
        table.add_column("CONNECT")

        for host in _settings.REMOTE_HOSTS:
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
        console.print(table)


class DiscoverEvaluators(CMD):
    """ Command to list all challenges"""

    def __init__(self, cmd_path):
        super(DiscoverEvaluators, self).__init__(cmd_path)
        self.parser.add_argument('host')

    @property
    def name(self) -> str:
        return 'discover'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.host not in _settings.REMOTE_HOSTS:
            console.print(":x: Error specified host was not found", style="red")
            sys.exit(1)

        remote_dir = _settings.REMOTE_BIN.get(args.host, None)
        if remote_dir is None:
            console.print(":x: Error specified host does not have a known bin dir", style="red")
            sys.exit(2)

        evaluators = misc.discover_evaluators(args.host, remote_dir)
        # show
        console.print(f"Found evaluators : {[ev.label for ev in evaluators]}")
        response = Confirm.ask("Do want to import them into the database?")
        if response:
            asyncio.run(ch_queries.add_evaluator(evaluators))
            console.print(":heavy_check_mark: successfully inserted evaluators")


def get() -> EvaluatorsCMD:
    evaluator = EvaluatorsCMD()

    evaluator.add_cmd(ListHostsEvaluators(evaluator.name))
    evaluator.add_cmd(ListRegisteredEvaluators(evaluator.name))
    evaluator.add_cmd(DiscoverEvaluators(evaluator.name))

    return evaluator
