import asyncio
import json
import string
import sys
import time
from pathlib import Path

from pydantic import EmailStr
from rich.progress import Progress, BarColumn
from rich.table import Table

from zerospeech import out, get_settings
from zerospeech.admin.cli.cmd_types import CommandCollection, CMD
from zerospeech.db.q import users as user_q
from zerospeech.utils import notify


_settings = get_settings()


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
        self.parser.add_argument("-m", "--mail-list", action='store_true')

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

        if args.mail_list:
            for u in user_lst:
                if u.active and u.verified == 'True':
                    out.Console.print(f"{u.username} {u.email}")
            sys.exit(0)

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

        out.Console.print(table)


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
    def just_print():
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

        out.Console.print(table)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.close:
            asyncio.run(user_q.delete_session(by_uid=args.close))
            out.Console.print(f"All sessions of user {args.close} were closed", style="bold")
        elif args.close_all:
            asyncio.run(user_q.delete_session(clear_all=True))
            out.Console.print(f"All sessions were closed", style="bold")
        else:
            self.just_print()


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

    def _create_form_input(self, progress):

        out.Console.print("-- New User Info --", style="bold")
        first_name = out.Console.console.input("First Name: ")
        last_name = out.Console.console.input("Last Name: ")
        email = out.Console.console.input("Email: ")
        affiliation = out.Console.console.input("Affiliation: ")

        clean_last_name = ''.join([i if i in string.ascii_letters else ' ' for i in last_name])
        def_username = f"{first_name[0]}{clean_last_name.replace(' ', '')}".lower()
        username = out.Console.console.input(f"Username(default {def_username}): ")
        username = username if username else def_username

        password = out.Console.console.input("Password: ", password=True)

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
        with Progress("[progress.description]{task.description}",
                      BarColumn(), "[progress.percentage]"
                      ) as progress:

            if args.from_file:
                json_file = Path(args.from_file)
                if not json_file.is_file() or json_file.suffix != ".json":
                    out.Console.print(f":x: Input: {json_file} does not exist or is not a valid json file.")
                    sys.exit(1)
                self._create_from_file(json_file, progress)
            else:
                self._create_form_input(progress)


class VerifyUser(CMD):
    """ User verification """

    def __init__(self, cmd_path):
        super(VerifyUser, self).__init__(cmd_path)
        self.parser.add_argument("-v", "--verify", metavar="UID", type=int,
                                 help="verify a specific user")
        self.parser.add_argument("--verify-all", action='store_true', help="verify all users")
        self.parser.add_argument("-s", "--send", metavar="UID", type=int,
                                 help="resend verification email to unverified user")
        self.parser.add_argument("--send-all", action='store_true',
                                 help="resend verification email to all unverified users")

    @property
    def name(self) -> str:
        return 'verify'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.verify:
            # verify user
            asyncio.run(user_q.admin_verification(args.verify))
        elif args.verify_all:
            # verify all users
            users = asyncio.run(user_q.get_user_list())
            for u in users:
                if u.verified != 'True':
                    asyncio.run(user_q.admin_verification(u.id))
        elif args.send:
            # send verification email
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.Console.error("Path file not found in settings")
                sys.exit(1)

            try:
                user = asyncio.run(user_q.get_user(by_uid=args.send))
            except ValueError:
                out.Console.error(f"User with id: {args.send} does not exist !!")
                sys.exit(1)

            if user.verified != 'True':
                asyncio.run(notify.email.template_email(
                    emails=[user.email],
                    subject='[Zerospeech] Account Verification',
                    data=dict(
                        username=user.username,
                        admin_email=_settings.admin_email,
                        url=f"{_settings.API_BASE_URL}{verification_path}?v={user.verified}&username={user.username}"
                    ),
                    template_name='email_validation.jinja2'
                ))
            else:
                out.Console.error(f"User {user.username} is already verified !!")
                sys.exit(1)

        elif args.send_all:
            # send all emails for verification
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.Console.error("Path file not found in settings")
                sys.exit(1)

            users = asyncio.run(user_q.get_user_list())
            for u in users:
                if u.verified != 'True':
                    asyncio.run(notify.email.template_email(
                        emails=[u.email],
                        subject='[Zerospeech] Account Verification',
                        data=dict(
                            username=u.username,
                            admin_email=_settings.admin_email,
                            url=f"{_settings.API_BASE_URL}{verification_path}?v={u.verified}&username={u.username}"
                        ),
                        template_name='email_validation.jinja2'
                    ))
        else:
            self.parser.print_help()


class ActivationUser(CMD):
    """ User activation/deactivation """

    def __init__(self, cmd_path):
        super(ActivationUser, self).__init__(cmd_path)
        self.parser.add_argument("-a", "--activate", metavar="UID",
                                 help="activate a specific user")
        self.parser.add_argument("-d", "--deactivate", metavar="UID",
                                 help="deactivate a specific user")
        self.parser.add_argument("--activate-all", action='store_true', help="activate all users")
        self.parser.add_argument("--deactivate-all", action='store_true', help="deactivate all users")

    @property
    def name(self) -> str:
        return 'status'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.activate:
            # activate user
            asyncio.run(user_q.toggle_user_status(args.activate, True))
            out.Console.info("User activated successfully")
        elif args.deactivate:
            # deactivate user
            asyncio.run(user_q.toggle_user_status(args.deactivate, False))
            out.Console.info("User deactivated successfully")
        elif args.activate_all:
            # activate all users
            asyncio.run(user_q.toggle_all_users_status(True))
            out.Console.info("Users activated successfully")
        elif args.deactivate_all:
            # deactivate all users
            asyncio.run(user_q.toggle_all_users_status(False))
            out.Console.info("Users deactivated successfully")
        else:
            self.parser.print_help()


class PasswordUser(CMD):
    """Password reset sessions """

    def __init__(self, cmd_path):
        super(PasswordUser, self).__init__(cmd_path)
        self.parser.add_argument("-r", "--reset", metavar="UID",
                                 help="reset & send a new password session to user")

    @property
    def name(self) -> str:
        return 'password'

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.reset:
            try:
                with (_settings.DATA_FOLDER / 'password_reset.path').open() as fp:
                    password_reset_path = fp.read()
            except FileNotFoundError:
                out.Console.error("Path file not found in settings")
                sys.exit(1)

            user = asyncio.run(user_q.get_user(by_uid=args.reset))
            session = asyncio.run(user_q.create_password_reset_session(user.username, user.email))
            asyncio.run(notify.email.template_email(
                emails=[user.email],
                subject='[Zerospeech] Password Reset',
                data=dict(
                    username=user.username,
                    url=f"{_settings.API_BASE_URL}{password_reset_path}?v={session.token}",
                    admin_email=_settings.admin_email
                ),
                template_name='password_reset.jinja2'
            ))
        else:
            self.parser.print_help()


def get() -> UsersCMD:
    users = UsersCMD()
    users.add_cmd(ListUsers(users.name))
    users.add_cmd(LoggedUsers(users.name))
    users.add_cmd(CreateUser(users.name))
    users.add_cmd(VerifyUser(users.name))
    users.add_cmd(ActivationUser(users.name))
    users.add_cmd(PasswordUser(users.name))
    return users
