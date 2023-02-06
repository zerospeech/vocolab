import asyncio
import json
import string
import sys
from pathlib import Path
from typing import Tuple

from pydantic import EmailStr
from rich.prompt import Prompt
from rich.table import Table

from vocolab import out, get_settings
from vocolab.core import notify, cmd_lib
from vocolab.data import models, model_queries

_settings = get_settings()


class UsersCMD(cmd_lib.CMD):
    """ Command for user administration (default: list)"""

    def __init__(self, root, name, cmd_path):
        super(UsersCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-m", "--mail-list", action='store_true',
                                 help="List active users in a CSV (username, email) format")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        # fetch data
        user_lst: model_queries.UserList = asyncio.run(model_queries.UserList.get())

        if args.mail_list:
            for u in user_lst:
                if u.active and u.verified == 'True':
                    out.cli.print(f"{u.username} {u.email}")
            sys.exit(0)

        # Prepare output
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID")
        table.add_column("Username")
        table.add_column("Email")
        table.add_column("Active")
        table.add_column("Verified")
        table.add_column("Created")

        for usr in user_lst:
            created = usr.created_at.isoformat() if usr.created_at else None
            table.add_row(
                f"{usr.id}", usr.username, usr.email, f"{usr.active}", f"{usr.verified}",
                f"{created}"
            )

        out.cli.print(table)


class CreateUserSessionCMD(cmd_lib.CMD):
    """ Create a session for a user """

    def __init__(self, root, name, cmd_path):
        super(CreateUserSessionCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("user_id", type=int)

    @staticmethod
    async def login(user_id: int) -> Tuple[str, str, str]:
        user = await model_queries.User.get(by_uid=user_id)
        token = model_queries.Token(
            user_email=user.email
        )
        return token.encode(), user.username, user.email

    def run(self, argv):
        args = self.parser.parse_args(argv)
        token, username, email = asyncio.run(
            self.login(args.user_id)
        )
        out.cli.print(f"{username}, {email}, {token}")
        sys.exit(0)


class CreateUserCMD(cmd_lib.CMD):
    """ Create new users """

    def __init__(self, root, name, cmd_path):
        super(CreateUserCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-f', '--from-file', type=str, help="Load users from a json file")

    @staticmethod
    def _make_usr(user: models.api.UserCreateRequest):
        _ = asyncio.run(model_queries.User.create(new_usr=user))

    def _create_from_file(self, file: Path):
        with file.open() as fp:
            user_list = json.load(fp)

            for data in user_list:
                user = models.api.UserCreateRequest(
                    username=data.get("username"),
                    email=EmailStr(data.get('email')),
                    pwd=data.get("password"),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    affiliation=data.get('affiliation')
                )
                self._make_usr(user)

    def _create_form_input(self):

        out.cli.print("-- New User Info --", style="bold")
        first_name = out.cli.raw.input("First Name: ")
        last_name = out.cli.raw.input("Last Name: ")
        email = out.cli.raw.input("Email: ")
        affiliation = out.cli.raw.input("Affiliation: ")

        clean_last_name = ''.join([i if i in string.ascii_letters else ' ' for i in last_name])
        def_username = f"{first_name[0]}{clean_last_name.replace(' ', '')}".lower()
        username = out.cli.raw.input(f"Username(default {def_username}): ")
        username = username if username else def_username

        password = out.cli.raw.input("Password: ", password=True)

        user = models.api.UserCreateRequest(
            username=username,
            email=EmailStr(email),
            pwd=password,
            first_name=first_name,
            last_name=last_name,
            affiliation=affiliation
        )
        self._make_usr(user)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.from_file:
            json_file = Path(args.from_file)
            if not json_file.is_file() or json_file.suffix != ".json":
                out.cli.print(f":x: Input: {json_file} does not exist or is not a valid json file.")
                sys.exit(1)
            self._create_from_file(json_file)
        else:
            self._create_form_input()


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

    @staticmethod
    async def verify_single(user_id: int):
        user = await model_queries.User.get(by_uid=user_id)
        await user.verify(verification_code=user.verified, force=True)

    @staticmethod
    async def verify_all():
        await model_queries.UserList.verify()

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.verify:
            # verify user
            asyncio.run(self.verify_single(user_id=args.verify))
        elif args.verify_all:
            # verify all users
            asyncio.run(self.verify_all())
        elif args.send:
            # send verification email
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.cli.error("Path file not found in settings")
                sys.exit(1)

            try:
                user = asyncio.run(model_queries.User.get(by_uid=args.send))
            except ValueError:
                out.cli.error(f"User with id: {args.send} does not exist !!")
                sys.exit(1)

            if user.verified != 'True':
                asyncio.run(notify.email.template_email(
                    emails=[user.email],
                    subject='[Zerospeech] Account Verification',
                    data=dict(
                        username=user.username,
                        admin_email=_settings.app_options.admin_email,
                        url=f"{_settings.api_options.API_BASE_URL}{verification_path}?v={user.verified}&username={user.username}"
                    ),
                    template_name='email_validation.jinja2'
                ))
            else:
                out.cli.error(f"User {user.username} is already verified !!")
                sys.exit(1)

        elif args.send_all:
            # send all emails for verification
            try:
                with (_settings.DATA_FOLDER / 'email_verification.path').open() as fp:
                    verification_path = fp.read()
            except FileNotFoundError:
                out.cli.error("Path file not found in settings")
                sys.exit(1)

            users = asyncio.run(model_queries.UserList.get())
            for u in users:
                if u.verified != 'True':
                    asyncio.run(notify.email.template_email(
                        emails=[u.email],
                        subject='[Zerospeech] Account Verification',
                        data=dict(
                            username=u.username,
                            admin_email=_settings.app_options.admin_email,
                            url=f"{_settings.api_options.API_BASE_URL}{verification_path}?v={u.verified}&username={u.username}"
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

    @staticmethod
    async def toggle_status(user_id: int, activate: bool):
        user = await model_queries.User.get(by_uid=user_id)
        await user.toggle_status(active=activate)

    @staticmethod
    async def toggle_all(activate: bool):
        await model_queries.UserList.toggle_status(active=activate)

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.activate:
            # activate user
            asyncio.run(self.toggle_status(user_id=args.activate, activate=True))
            out.cli.info("User activated successfully")
        elif args.deactivate:
            # deactivate user
            asyncio.run(self.toggle_status(user_id=args.activate, activate=False))
            out.cli.info("User deactivated successfully")
        elif args.activate_all:
            # activate all users
            asyncio.run(self.toggle_all(activate=True))
            out.cli.info("Users activated successfully")
        elif args.deactivate_all:
            # deactivate all users
            asyncio.run(self.toggle_all(activate=False))
            out.cli.info("Users deactivated successfully")
        else:
            self.parser.print_help()


class PasswordUserCMD(cmd_lib.CMD):
    """Password reset sessions """

    def __init__(self, root, name, cmd_path):
        super(PasswordUserCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-r", "--reset", metavar="UID",
                                 help="reset & send a new password session to user")

    @staticmethod
    async def reset_password_session(user_id):
        user = await model_queries.User.get(by_uid=user_id)
        token = model_queries.Token(
            allow_password_reset=True,
            user_email=user.email
        )
        return token.encode(), user.username, user.email

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.reset:
            try:
                with (_settings.DATA_FOLDER / 'password_reset.path').open() as fp:
                    password_reset_path = fp.read()
            except FileNotFoundError:
                out.cli.error("Path file not found in settings")
                sys.exit(1)

            token, username, email = asyncio.run(self.reset_password_session(args.reset))
            asyncio.run(notify.email.template_email(
                emails=[email],
                subject='[Zerospeech] Password Reset',
                data=dict(
                    username=username,
                    url=f"{_settings.api_options.API_BASE_URL}{password_reset_path}?v={token}",
                    admin_email=_settings.app_options.admin_email
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

    @staticmethod
    async def check_password(user_id: int, password: str):
        user = await model_queries.User.get(by_uid=user_id)
        return user.password_matches(password)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        pwd = Prompt.ask('password', password=True)
        if asyncio.run(self.check_password(args.user_id, pwd)):
            out.cli.info("--> Passwords match !!")
            sys.exit(0)
        else:
            out.cli.error("--> Passwords do not match !!")
            sys.exit(1)


class NotifyCMD(cmd_lib.CMD):
    """ Notify all users """

    def __init__(self, root, name, cmd_path):
        super(NotifyCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-s', '--subject', type=str, default='',
                                 help="The subject of the email")
        self.parser.add_argument("body", type=Path, help="A text file containing the body of the email.")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        user_list = asyncio.run(model_queries.UserList.get())
        email_list = [user.email for user in user_list]
        with args.body.open() as fp:
            body = fp.read()

        asyncio.run(notify.email.simple_html_email(
            emails=email_list, subject=f"[ZEROSPEECH] {args.subject}",
            content=body
        ))


class DeleteUser(cmd_lib.CMD):
    """ Delete a user"""

    def __init__(self, root, name, cmd_path):
        super(DeleteUser, self).__init__(root, name, cmd_path)
        # custom args
        self.parser.add_argument('user_id', type=int, help="User id of the user")
        self.parser.add_argument('--save', help="path to save user details as info")

    @staticmethod
    async def delete_user(user_id: int):
        pass
        # user_submissions = await challengesQ.list_submission(by_user=user_id)
        # if len(user_submissions) > 0:
        #     out.cli.print(f"User {user_id} has {len(user_submissions)} unarchived submissions !!\n"
        #                   f"Cannot delete, archive submissions and try again !!")
        #     sys.exit(1)
        #
        # user = await userQ.get_user(by_uid=user_id)
        # user_dict = user.dict()
        #
        # await userQ.delete_session(by_uid=user_id)
        # await userQ.clear_password_reset_sessions(by_uid=user_id)
        # await userQ.delete_user(uid=user_id)
        # return user_dict

    def run(self, argv):
       pass
        # args = self.parser.parse_args(argv)
        # user_dict = asyncio.run(self.delete_user(args.user_id))
        # out.cli.info(f'User {args.user_id} deleted successfully !!')
        #
        # if args.save:
        #     out.cli.info(f"backing up user @ {args.save}")
        #     with Path(args.save).with_suffix('.json').open('w') as fp:
        #         json.dump(user_dict, fp, cls=CustomTypesJsonEncoder)
