from os import execv
from shutil import which

from zerospeech import get_settings, out
from zerospeech.admin import cmd_lib
from zerospeech.db.base import create_db

_settings = get_settings()


class APICMD(cmd_lib.CMD):
    """ Command for api instance administration """
    
    def __init__(self, root, name, cmd_path):
        super(APICMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()


class DebugAPICMD(cmd_lib.CMD):
    """ Run debug instance of API using uvicorn """

    def __init__(self, root, name, cmd_path):
        super(DebugAPICMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("-u", "--uvicorn", action='store_true',
                                 help="Pass custom arguments to uvicorn")
        self.parser.add_argument("-o", "--uvicorn-options", action='store_true',
                                 help="Print uvicorn command options")

    def run(self, argv):
        args, extra_args = self.parser.parse_known_args(argv)

        executable = which('uvicorn')
        exec_args = [f'{executable}']

        if args.uvicorn_options:
            # run help on the uvicorn command
            exec_args.extend(['--help'])
        elif args.uvicorn:
            # run with custom uvicorn options
            exec_args.extend(['zerospeech.api:app', *extra_args])
        else:
            # run default debug version
            exec_args.extend(['zerospeech.api:app', '--reload', '--debug', '--no-access-log'])

        execv(executable, exec_args)
        
        
class APInitEnvironmentCMD(cmd_lib.CMD):
    """ Initialise components needed for the API """
    
    def __init__(self, root, name, cmd_path):
        super(APInitEnvironmentCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)

        # create data_folders
        out.Console.info(f"creating : {_settings.USER_DATA_DIR}")
        _settings.USER_DATA_DIR.mkdir(exist_ok=True, parents=True)
        out.Console.info(f"creating : {_settings.USER_DATA_DIR / 'submissions'}")
        (_settings.USER_DATA_DIR / 'submissions').mkdir(exist_ok=True)
        out.Console.info(f"creating : {_settings.USER_DATA_DIR / 'profiles'}")
        (_settings.USER_DATA_DIR / 'profiles').mkdir(exist_ok=True)
        out.Console.info(f"creating : {_settings.LEADERBOARD_LOCATION}")
        _settings.LEADERBOARD_LOCATION.mkdir(exist_ok=True)

        # create tables
        out.Console.info(f"creating : tables in database ...")
        create_db()


# TODO create gunicorn config generation
# TODO create gunicorn wrapper cli
