import os
import shlex
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from vocolab import out, get_settings
from vocolab.admin import cmd_lib
from vocolab.db.models import tasks
from vocolab.worker import server

_settings = get_settings()


class TaskWorkerCMD(cmd_lib.CMD):
    """ Administrate Task Workers """

    def __init__(self, root, name, cmd_path):
        super(TaskWorkerCMD, self).__init__(root, name, cmd_path)
        self.parser.description = """Inspect Celery Tasks & Workers
actions:
    - tasks: list registered tasks
    - list active queues
    - list active tasks
    - list reserved tasks (running in a worker)
        """

        self.parser.add_argument('action', choices=['tasks', 'queues', 'active', 'reserved'])

    def run(self, argv):
        args = self.parser.parse_args(argv)
        if args.action == 'tasks':
            out.cli.print("List of registered tasks :", style="bold red")
            out.cli.info([k for k, _ in server.app.tasks.items() if "celery" not in k])
        elif args.action == 'queues':
            out.cli.print("List of active queues :", style="bold red")
            out.cli.info(server.app.control.inspect().active_queues())
        elif args.action == 'active':
            out.cli.print("List of waiting tasks :", style="bold red")
            out.cli.info(server.app.control.inspect().active())
        elif args.action == 'reserved':
            out.cli.print("List of running tasks :", style="bold red")
            out.cli.info(server.app.control.inspect().reserved())


class SendEchoMessage(cmd_lib.CMD):
    """ Send a test message to the echo worker server """

    def __init__(self, root, name, cmd_path):
        super(SendEchoMessage, self).__init__(root, name, cmd_path)
        self.parser.add_argument("message", type=str)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        server.echo().delay(
            tasks.SimpleLogMessage(
                label="cli-echo-testing",
                message=f"{args.message}"
            ).dict()
        )
        out.cli.info('Message delivered successfully !!')


class GenerateWorkerCMD(cmd_lib.CMD):
    """ Generate files allowing to configure workers"""
    
    def __init__(self, root, name, cmd_path):
        super(GenerateWorkerCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        self.parser.print_help()


class GenerateWorkerSettings(cmd_lib.CMD):
    """ Generate a template systemD unit file to manage workers daemon """

    def __init__(self, root, name, cmd_path):
        super(GenerateWorkerSettings, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--output-file', type=str, help="File to output result config")
        self.parser.add_argument('worker_type', choices=['eval', 'update'])
        self.config_file = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR)) \
            .get_template("worker.config")

    def run(self, argv):
        args, extra_args = self.parser.parse_known_args(argv)

        if args.worker_type == 'eval':
            node_name = _settings.celery_options.celery_nodes.get('eval')
            queue_name = _settings.QUEUE_CHANNELS.get('eval')
        else:
            node_name = _settings.celery_options.celery_nodes['update']
            queue_name = _settings.QUEUE_CHANNELS.get('update')

        config_data = dict(
            node_name=node_name,
            celery_bin=_settings.celery_options.celery_bin,
            app_module=_settings.celery_options.celery_app,
            workDirectory=_settings.DATA_FOLDER,
            pool_type=_settings.celery_options.celery_pool_type,
            concurrency=_settings.celery_options.celery_worker_number,
            queue_name=queue_name,
            extra_options=shlex.join(extra_args),
            CUSTOM_PATH=os.environ.get('PATH'),
            ZR_ENV_FILE=os.environ.get('ZR_ENV_FILE'),
            log_level="INFO"
        )
        # export
        if args.output_file:
            with Path(args.output_file).open("w") as fp:
                fp.write(self.config_file.render(**config_data))
        else:
            out.cli.raw.out(self.config_file.render(**config_data))


class GenerateSystemDUnit(cmd_lib.CMD):
    """ Generate a template systemD unit file to manage workers daemon """

    def __init__(self, root, name, cmd_path):
        super(GenerateSystemDUnit, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-o', '--output-file', type=str, help="File to output result config")
        self.parser.add_argument('config_location')
        self.unit_template = Environment(loader=FileSystemLoader(_settings.CONFIG_TEMPLATE_DIR)) \
            .get_template("worker.service")

    def run(self, argv):
        args = self.parser.parse_args(argv)

        config_location = Path(args.config_location).resolve()

        if not config_location.is_file():
            out.cli.error(f"ERROR: Specified config file does not exist ({config_location})")
            sys.exit(1)

        systemd_unit_data = dict(
            user=_settings.SERVICE_USER,
            group=_settings.SERVICE_GROUP,
            workDirectory=_settings.DATA_FOLDER,
            environmentFile=str(config_location)
        )

        # export
        if args.output_file:
            with Path(args.output_file).open("w") as fp:
                fp.write(self.unit_template.render(**systemd_unit_data))
        else:
            out.cli.raw.out(self.unit_template.render(**systemd_unit_data))
