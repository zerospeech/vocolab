import asyncio
import json
import string
import sys
import time
from pathlib import Path

from pydantic import EmailStr
from rich.console import Console
from rich.progress import Progress, BarColumn
from rich.table import Table

from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import users as user_q


class UsersCMD(CommandCollection):
    __cmd_list__ = {}

    @property
    def description(self) -> str:
        return 'command group to administrate users'

    @property
    def name(self) -> str:
        return 'users'


class ListUsers(CMD):

    def __init__(self, cmd_path):
        super(ListUsers, self).__init__(cmd_path)

    @property
    def name(self) -> str:
        return 'list'

    @property
    def short_description(self):
        return 'lists available users'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        user_lst = asyncio.run(user_q.get_user_list())

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


class LoggedUsers(CMD):

    def __init__(self, cmd_path):
        super(LoggedUsers, self).__init__(cmd_path)
        self.parser.add_argument("--close", type=int, help="user to close sessions of")
        self.parser.add_argument("--close-all", action='store_true',
                                 help="close all open sessions")

    @property
    def name(self) -> str:
        return 'logged'

    @property
    def short_description(self):
        return "list logged users"

    @staticmethod
    def just_print(console):
        """ Prints a list of logged users """
        user_lst = asyncio.run(user_q.get_logged_user_list())

        # Prepare output
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

    def run(self, argv):
        args = self.parser.parse_args(argv)
        console = Console()

        if args.close:
            asyncio.run(user_q.delete_session(by_uid=args.close))
            console.print(f"All sessions of user {args.close} were closed", style="bold")
        elif args.close_all:
            asyncio.run(user_q.delete_session(clear_all=True))
            console.print(f"All sessions were closed", style="bold")
        else:
            self.just_print(console)


class CreateUser(CMD):

    def __init__(self, cmd_path):
        super(CreateUser, self).__init__(cmd_path)
        self.parser.add_argument('-f', '--from-file', type=str, help="Load users from a json file")

    @property
    def name(self) -> str:
        return 'create'

    @property
    def short_description(self):
        return "create a new user"

    @staticmethod
    def _make_usr(user: user_q.UserCreate, progress):
        task = progress.add_task(f"[red]--> Creating...{user.username}", start=False)
        time.sleep(1)
        _ = asyncio.run(user_q.create_user(user))
        progress.update(task, completed=True,
                        description=f"[bold][green]:heavy_check_mark: User "
                                    f"{user.username} Created Successfully[/green][/bold]")

    def _create_from_file(self, file: Path, progress):
        with file.open() as fp:
            user_list = json.load(fp)
            task1 = progress.add_task("[red]Creating users...", total=len(user_list))

            for data in user_list:
                progress.update(task1, advance=0.5)
                user = user_q.UserCreate(
                    username=data.get("username"),
                    email=EmailStr(data.get('email')),
                    pwd=data.get("password"),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    affiliation=data.get('affiliation')
                )
                self._make_usr(user, progress)
                progress.update(task1, advance=0.5)

    def _create_form_input(self, console, progress):
        console.print("-- New User Info --", style="bold")
        first_name = console.input("First Name: ")
        last_name = console.input("Last Name: ")
        email = console.input("Email: ")
        affiliation = console.input("Affiliation: ")

        clean_last_name = ''.join([i if i in string.ascii_letters else ' ' for i in last_name])
        def_username = f"{first_name[0]}{clean_last_name.replace(' ', '')}".lower()
        username = console.input(f"Username(default {def_username}): ")
        username = username if username else def_username

        password = console.input("Password: ", password=True)

        user = user_q.UserCreate(
            username=username,
            email=EmailStr(email),
            pwd=password,
            first_name=first_name,
            last_name=last_name,
            affiliation=affiliation
        )
        self._make_usr(user, progress)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        console = Console()
        with Progress("[progress.description]{task.description}",
                      BarColumn(), "[progress.percentage]"
                      ) as progress:

            if args.from_file:
                json_file = Path(args.from_file)
                if not json_file.is_file() or json_file.suffix != ".json":
                    console.print(f":x: Input: {json_file} does not exist or is not a valid json file.")
                    sys.exit(1)
                self._create_from_file(json_file, progress)
            else:
                self._create_form_input(console, progress)


# todo: new user
# todo: deactivate
# todo: get_all_date
# todo: reset credentials


def get() -> UsersCMD:
    users = UsersCMD()
    users.add_cmd(ListUsers(users.name))
    users.add_cmd(LoggedUsers(users.name))
    users.add_cmd(CreateUser(users.name))
    return users
