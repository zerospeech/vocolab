import os
import shutil
import sys
from os import execv
from pathlib import Path
from shutil import which
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader

from vocolab import get_settings, out
from vocolab.admin import cmd_lib
from vocolab.db.base import create_db

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
        exec_args = []

        if args.uvicorn_options:
            # run help on the uvicorn command
            exec_args.extend(['--help'])
        elif args.uvicorn:
            # run with custom uvicorn options
            exec_args.extend(['vocolab.api:app', *extra_args])
        else:
            # run default debug version
            exec_args.extend(['vocolab.api:app', '--reload', '--debug', '--no-access-log'])

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
            out.cli.error("Fail")

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
        out.cli.info(f"creating : {_settings.user_data_dir}")
        _settings.user_data_dir.mkdir(exist_ok=True, parents=True)
        out.cli.info(f"creating : {_settings.submission_dir}")
        _settings.submission_dir.mkdir(exist_ok=True)
        out.cli.info(f"creating : {_settings.leaderboard_dir}")
        _settings.leaderboard_dir.mkdir(exist_ok=True)
        # create tables
        out.cli.info(f"creating : tables in database ...")
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
        self.template = Environment(loader=FileSystemLoader(_settings.config_template_dir))\
            .get_template("gunicorn_app.wsgi")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        data = dict(
            wsgi_app=_settings.server_options.WSGI_APP,
            zr_env_file=os.environ.get('VOCO_CFG', ''),
            worker_class=_settings.server_options.GUNICORN_WORKER_CLASS,
            nb_workers=_settings.server_options.GUNICORN_WORKERS,
            bind_point=_settings.server_options.SERVER_BIND
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
                fp.write('\n')
        else:
            out.cli.raw.out(self.template.render(**data))


class SystemDSocketFileGeneration(cmd_lib.CMD):
    """ Generate a template SystemD socket unit file """

    def __init__(self, root, name, cmd_path):
        super(SystemDSocketFileGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.template = Environment(loader=FileSystemLoader(_settings.config_template_dir))\
            .get_template("gunicorn.socket")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        bind = urlparse(_settings.server_options.SERVER_BIND)
        if bind.scheme == 'unix':
            socket_file = bind.path
        else:
            out.cli.warning('There is no socket bind in configurations')
            sys.exit(1)

        data = dict(
            socket_user=_settings.server_options.NGINX_USER,
            socket_file=socket_file
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
                fp.write('\n')
        else:
            out.cli.raw.out(self.template.render(**data))


class SystemDUnitGeneration(cmd_lib.CMD):
    """ Generate a template SystemD unit file to manage api daemon """

    def __init__(self, root, name, cmd_path):
        super(SystemDUnitGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.parser.add_argument('gunicorn_config_file', type=str, help="File to configure gunicorn with")
        self.template = Environment(loader=FileSystemLoader(_settings.config_template_dir), trim_blocks=True)\
            .get_template("api.service")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        gunicorn_cfg_file = Path(args.gunicorn_config_file)

        if not gunicorn_cfg_file.is_file():
            out.cli.error(f'Config given : {gunicorn_cfg_file} ! Error no such file found ')
            sys.exit(1)

        bind = urlparse(_settings.server_options.SERVER_BIND)
        has_socket = bind.scheme == "unix"

        data = dict(
            user=_settings.server_options.SERVICE_USER,
            group=_settings.server_options.SERVICE_GROUP,
            run_dir=_settings.DATA_FOLDER,
            gunicorn_exe=shutil.which('gunicorn'),
            gunicorn_cmd=f"-c {gunicorn_cfg_file.resolve()}",
            has_socket=has_socket
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
                fp.write('\n')
        else:
            out.cli.raw.out(self.template.render(**data))


class NginxConfigGeneration(cmd_lib.CMD):
    """ Generate a template Nginx server file """

    def __init__(self, root, name, cmd_path):
        super(NginxConfigGeneration, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--out-file', type=str, help="File to output result config")
        self.template = Environment(loader=FileSystemLoader(_settings.config_template_dir), trim_blocks=True)\
            .get_template("nginx.conf")

    def run(self, argv):
        args = self.parser.parse_args(argv)
        default_url = urlparse(_settings.API_BASE_URL)
        data = dict(
            url=f"{default_url.netloc}{default_url.path}",
            bind_url=_settings.server_options.SERVER_BIND,
            access_log=f"/var/log/nginx/api_access.log",
            error_log=f"/var/log/nginx/api_error.log"
        )
        # export
        if args.out_file:
            with Path(args.out_file).open("w") as fp:
                fp.write(self.template.render(**data))
                fp.write('\n')
        else:
            out.cli.raw.out(self.template.render(**data))
