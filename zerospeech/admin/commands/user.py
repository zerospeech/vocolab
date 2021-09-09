import asyncio
import json
import string
import sys
import time
from pathlib import Path

from pydantic import EmailStr
from rich.progress import Progress, BarColumn
from rich.prompt import Prompt
from rich.table import Table

from zerospeech import out, get_settings
from zerospeech.admin import cmd_lib
from zerospeech.db.models.misc import UserCreate
from zerospeech.db.q import userQ
from zerospeech.lib import notify


_settings = get_settings()


class UsersCMD(cmd_lib.CMD):
    """ Command for user administration (default: list)"""

    def __init__(self, root, name, cmd_path):
        super(UsersCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-m", "--mail-list", action='store_true')

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        user_lst = asyncio.run(userQ.get_user_list())

        if args.mail_list:
            for u in user_lst:
                if u.active and u.verified == 'True':
                    out.print(f"{u.username} {u.email}")
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

        out.print(table)


class UserSessionsCMD(cmd_lib.CMD):
    """ List logged users """

    def __init__(self, root, name, cmd_path):
        super(UserSessionsCMD, self).__init__(root, name, cmd_path)

    @staticmethod
    def just_print():
        """ Prints a list of logged users """
        user_lst = asyncio.run(userQ.get_logged_user_list())

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

        out.print(table)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.just_print()


class CloseUserSessionsCMD(cmd_lib.CMD):
    """ Close user sessions """

    def __init__(self, root, name, cmd_path):
        super(CloseUserSessionsCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-u", "--user-id")
        self.parser.add_argument("-a", "--close-all", action='store_true')

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.user_id:
            asyncio.run(userQ.delete_session(by_uid=args.user_id))
            out.print(f"All sessions of user {args.user_id} were closed", style="bold")
        elif args.close_all:
            asyncio.run(userQ.delete_session(clear_all=True))
            out.print(f"All sessions were closed", style="bold")
        else:
            self.parser.print_help()

        sys.exit(0)


class CreateUserSessionsCMD(cmd_lib.CMD):
    """ Create a session for a user """

    def __init__(self, root, name, cmd_path):
        super(CreateUserSessionsCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("user_id", type=int)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        usr, token = asyncio.run(userQ.admin_login(by_uid=args.user_id))
        out.print(f"{usr.username}, {usr.email}, {token}")
        sys.exit(0)


class CreateUserCMD(cmd_lib.CMD):
    """ Create new users """

    def __init__(self, root, name, cmd_path):
        super(CreateUserCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-f', '--from-file', type=str, help="Load users from a json file")

    @staticmethod
    def _make_usr(user: UserCreate, progress):
        task = progress.add_task(f"[red]--> Creating...{user.username}", start=False)
        time.sleep(1)
        _ = asyncio.run(userQ.create_user(usr=user))
        progress.update(task, completed=True,
                        description=f"[bold][green]:heavy_check_mark: User "
                                    f"{user.username} Created Successfully[/green][/bold]")

    def _create_from_file(self, file: Path, progress):
        with file.open() as fp:
            user_list = json.load(fp)
            task1 = progress.add_task("[red]Creating users...", total=len(user_list))

            for data in user_list:
                progress.update(task1, advance=0.5)
                user = UserCreate(
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

        out.print("-- New User Info --", style="bold")
        first_name = out.input("First Name: ")
        last_name = out.input("Last Name: ")
        email = out.input("Email: ")
        affiliation = out.input("Affiliation: ")

        clean_last_name = ''.join([i if i in string.ascii_letters else ' ' for i in last_name])
        def_username = f"{first_name[0]}{clean_last_name.replace(' ', '')}".lower()
        username = out.input(f"Username(default {def_username}): ")
        username = username if username else def_username

        password = out.input("Password: ", password=True)

        user = UserCreate(
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
                    out.print(f":x: Input: {json_file} does not exist or is not a valid json file.")
                    sys.exit(1)
                self._create_from_file(json_file, progress)
            else:
                self._create_form_input(progress)


# todo create subcommand for various functions
class VerifyUserCMD(cmd_lib.CMD):
    """ User verification """

    def __init__(self, root, name, cmd_path):
        super(VerifyUserCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-v", "--verify", metavar="UID", type=int,
                                 help="verify a specific user")
        self.parser.add_argument("--verify-all", action='store_true', help="verify all users")
        self.parser.add_argument("-s", "--send", metavar="UID", type=int,
                                 help="resend verification email to unverified user")
        self.parser.add_argument("--send-all", action='store_true',
                                 help="resend verification email to all unverified users")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.verify:
            # verify user
            asyncio.run(userQ.admin_verification(user_id=args.verify))
        elif args.verify_all:
            # verify all users
            users = asyncio.run(userQ.get_user_list())
            for u in users:
                if u.verified != 'True':
                    asyncio.run(userQ.admin_verification(user_id=u.id))
        elif args.send:
            # send verification email
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.error("Path file not found in settings")
                sys.exit(1)

            try:
                user = asyncio.run(userQ.get_user(by_uid=args.send))
            except ValueError:
                out.error(f"User with id: {args.send} does not exist !!")
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
                out.error(f"User {user.username} is already verified !!")
                sys.exit(1)

        elif args.send_all:
            # send all emails for verification
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.error("Path file not found in settings")
                sys.exit(1)

            users = asyncio.run(userQ.get_user_list())
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


class UserActivationCMD(cmd_lib.CMD):
    """ User activation/deactivation """

    def __init__(self, root, name, cmd_path):
        super(UserActivationCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-a", "--activate", metavar="UID",
                                 help="activate a specific user")
        self.parser.add_argument("-d", "--deactivate", metavar="UID",
                                 help="deactivate a specific user")
        self.parser.add_argument("--activate-all", action='store_true', help="activate all users")
        self.parser.add_argument("--deactivate-all", action='store_true', help="deactivate all users")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.activate:
            # activate user
            asyncio.run(userQ.toggle_user_status(user_id=args.activate, active=True))
            out.info("User activated successfully")
        elif args.deactivate:
            # deactivate user
            asyncio.run(userQ.toggle_user_status(user_id=args.deactivate, active=False))
            out.info("User deactivated successfully")
        elif args.activate_all:
            # activate all users
            asyncio.run(userQ.toggle_all_users_status(active=True))
            out.info("Users activated successfully")
        elif args.deactivate_all:
            # deactivate all users
            asyncio.run(userQ.toggle_all_users_status(active=False))
            out.info("Users deactivated successfully")
        else:
            self.parser.print_help()


class PasswordUserCMD(cmd_lib.CMD):
    """Password reset sessions """

    def __init__(self, root, name, cmd_path):
        super(PasswordUserCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-r", "--reset", metavar="UID",
                                 help="reset & send a new password session to user")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.reset:
            try:
                with (_settings.DATA_FOLDER / 'password_reset.path').open() as fp:
                    password_reset_path = fp.read()
            except FileNotFoundError:
                out.error("Path file not found in settings")
                sys.exit(1)

            user = asyncio.run(userQ.get_user(by_uid=args.reset))
            out.ic(user)
            session = asyncio.run(userQ.create_password_reset_session(username=user.username, email=user.email))
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


class CheckPasswordCMD(cmd_lib.CMD):
    """ Check the password of a user """
    
    def __init__(self, root, name, cmd_path):
        super(CheckPasswordCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('user_id', type=int)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        pwd = Prompt.ask('password', password=True)

        user = asyncio.run(userQ.get_user(by_uid=args.user_id))
        if userQ.check_users_password(password=pwd, user=user):
            out.info("--> Passwords match !!")
            sys.exit(0)
        else:
            out.error("--> Passwords do not match !!")
            sys.exit(1)


class ResetSessionsCMD(cmd_lib.CMD):
    """ Check the list of reset sessions """
    
    def __init__(self, root, name, cmd_path):
        super(ResetSessionsCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('--all', action='store_true', help="Show all sessions (even expired ones)")
        self.parser.add_argument('--clean', action='store_true', help="Clean expired sessions")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.clean:
            # clean sessions
            asyncio.run(userQ.clear_expired_password_reset_sessions())
            out.info('removed all expired password reset sessions :heavy_check_mark:')
        else:
            sessions = asyncio.run(userQ.get_password_reset_sessions(args.all))
            # print
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("user_id")
            table.add_column("token")
            table.add_column("expiration_date")

            for item in sessions:
                table.add_row(
                    f"{item.user_id}", item.token, f"{item.expiration_date.isoformat()}"
                )

            out.print(table)


class NotifyCMD(cmd_lib.CMD):
    """ Notify all users """

    def __init__(self, root, name, cmd_path):
        super(NotifyCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-s', '--subject', type=str, default='',
                                 help="The subject of the email")
        self.parser.add_argument("body", type=Path, help="A text file containing the body of the email.")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        user_list = asyncio.run(userQ.get_user_list())
        email_list = [user.email for user in user_list]
        with args.body.open() as fp:
            body = fp.readlines()

        asyncio.run(notify.email.simple_html_email(
            emails=email_list, subject=f"[ZEROSPEECH] {args.subject}",
            content=""
        ))
        out.info(f'email sent to {[user.username for user in user_list]}')

