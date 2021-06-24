import os
import shutil
from os import execv
from pathlib import Path
from shutil import which
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader

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


class RunAPICMD(cmd_lib.CMD):
    """ Commands to run the api daemon """

    def __init__(self, root, name, cmd_path):
        super(RunAPICMD, self).__init__(root, name, cmd_path)

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


class ProdAPICMD(cmd_lib.CMD):
    """ Run production instance of API using gunicorn """

    def __init__(self, root, name, cmd_path):
        super(ProdAPICMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("configuration_file", help="Path to the config file")
        self.parser.add_argument("-g", "--gunicorn-args", action='store_true',
                                 help="Pass custom arguments to gunicorn")
        self.parser.add_argument("-o", "--gunicorn-options", action='store_true',
                                 help="Print gunicorn command options")

    def run(self, argv):
        args, extra_args = self.parser.parse_known_args(argv)
        conf_file = Path(args.configuration_file)
        if not conf_file.is_file():
            out.error("Fail")

        executable = which('gunicorn')
        exec_args = [f'{executable}']

        if args.uvicorn_options:
            # run help on the uvicorn command
            exec_args.extend(['--help'])
        elif args.uvicorn:
            # run with custom uvicorn options
            exec_args.extend([*extra_args, '-c', ])
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
        out.info(f"creating : {_settings.USER_DATA_DIR}")
        _settings.USER_DATA_DIR.mkdir(exist_ok=True, parents=True)
        out.info(f"creating : {_settings.USER_DATA_DIR / 'submissions'}")
        (_settings.USER_DATA_DIR / 'submissions').mkdir(exist_ok=True)
        out.info(f"creating : {_settings.USER_DATA_DIR / 'profiles'}")
        (_settings.USER_DATA_DIR / 'profiles').mkdir(exist_ok=True)
        out.info(f"creating : {_settings.LEADERBOARD_LOCATION}")
        _settings.LEADERBOARD_LOCATION.mkdir(exist_ok=True)

        # create tables
        out.info(f"creating : tables in database ...")
        create_db()


class ConfigFiles(cmd_lib.CMD):
    """ API Deployment config files """

    def __init__(self, root, name, cmd_path):
        super(ConfigFiles, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()


class GunicornConfigGeneration(cmd_lib.CMD):
    """ Generate a template gunicorn config file """
    
    def __init__(self, root, name, cmd_path):
        super(GunicornConfigGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.template = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR))\
            .get_template("gunicorn_app.wsgi")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        args_dict = vars(args)

        data = dict(
            wsgi_app=args_dict.get('wsgi_app', 'zerospeech.api:app'),
            zr_env_file=os.environ.get('ZR_ENV_FILE', ''),
            worker_class="uvicorn.workers.UvicornWorker",
            nb_workers=4,
            bind_point="127.0.1:5933"  # "unix:gunicorn.sock"
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
        else:
            out.console.out(self.template.render(**data))


class SystemDSocketFileGeneration(cmd_lib.CMD):
    """ Generate a template SystemD socket unit file """

    def __init__(self, root, name, cmd_path):
        super(SystemDSocketFileGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.parser.add_argument('-s', '--socket-user', type=str, help='User to read the socket file.')
        self.template = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR))\
            .get_template("gunicorn.socket")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        args_dict = vars(args)
        data = dict(
            socket_user=args_dict.get('socket_user', "www-data")
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
        else:
            out.console.out(self.template.render(**data))


class SystemDUnitGeneration(cmd_lib.CMD):
    """ Generate a template SystemD unit file to manage api daemon """

    def __init__(self, root, name, cmd_path):
        super(SystemDUnitGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.template = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR))\
            .get_template("api.service")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        args_dict = vars(args)
        data = dict(
            user=args_dict.get('user', 'zerospeech'),
            group=args_dict.get('group', 'zerospeech'),
            run_dir=args_dict.get('run_dir', '/zerospeech/app-data'),
            gunicorn_exe=args_dict.get('gunicorn_exe', shutil.which('gunicorn')),
            appfile=args_dict.get('gunicorn_exe', shutil.which('gunicorn')),
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
        else:
            out.console.out(self.template.render(**data))


class NginxConfigGeneration(cmd_lib.CMD):
    """ Generate a template Nginx server file """

    def __init__(self, root, name, cmd_path):
        super(NginxConfigGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.template = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR))\
            .get_template("nginx.conf")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        args_dict = vars(args)
        default_url = urlparse(_settings.API_BASE_URL)
        data = dict(
            url=args_dict.get('url', f"{default_url.netloc}{default_url.path}"),
            access_log=args_dict.get('access_log', f"/var/log/nginx/api_access.log"),
            error_log=args_dict.get('error_log', f"/var/log/nginx/api_error.log")
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
        else:
            out.console.out(self.template.render(**data))
