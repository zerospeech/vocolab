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


class EvaluatorsCMD(CommandCollection):
    """ Command to group actions on evaluator functions """
    __cmd_list__ = {}

    @property
    def name(self) -> str:
        return 'evaluator'


class ListEvaluators(CMD):
    """ Command to list all registered evaluators"""

    @property
    def name(self) -> str:
        return 'list'

    def __init__(self, cmd_path):
        super(ListEvaluators, self).__init__(cmd_path)

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
                f"{ev.id}", f"{ev.label}", f"{ev.executor}",
                f"{ev.script_path}", f"{ev.base_arguments.split(';')}"
            )

        # print
        console.print(table)


class DiscoverEvaluators(CMD):
    """ Command to list all challenges"""

    @property
    def name(self) -> str:
        return 'list'




def get() -> EvaluatorsCMD:
    evaluator = EvaluatorsCMD()
    evaluator.add_cmd(ListEvaluators(evaluator.name))

    return evaluator
