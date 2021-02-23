import asyncio
import argparse

from rich.console import Console
from rich.table import Table

from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import users as user_q


class UsersCMD(CommandCollection):

    @property
    def name(self) -> str:
        return 'users'


class ListUsers(CMD):

    def __init__(self, cmd_path):
        parser = argparse.ArgumentParser()

        super(ListUsers, self).__init__(parser, cmd_path)

    @property
    def name(self) -> str:
        return 'list'

    @property
    def short_description(self):
        return 'lists available users'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        loop = asyncio.get_event_loop()
        user_lst = loop.run_until_complete(user_q.get_user_list())

        # Prepare output
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("Username")
        table.add_column("Email")
        table.add_column("Active")
        table.add_column("Verified")

        for usr in user_lst:
            table.add_row(
                f"{usr.id}", usr.username, usr.email, f"{usr.active}", f"{usr.verified}"
            )

        console.print(table)


def get() -> UsersCMD:
    users = UsersCMD()
    users.add_cmd(ListUsers(users.name))
    return users
