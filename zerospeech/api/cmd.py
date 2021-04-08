import argparse
from os import execv
from shutil import which


def arg_parse(argv=None):
    parser = argparse.ArgumentParser(
        prog='zr-api',
        description="run debug localhost version of the API",
    )
    parser.add_argument('--no-reload', dest='reload', action='store_false',
                        help='deactivate auto-reload mode')
    parser.add_argument('--reload', dest='reload', action='store_true',
                        help='deactivate auto-reload mode')

    parser.add_argument('--no-debug', dest='debug', action='store_false',
                        help='deactivate debug mode')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='activate debug mode')

    parser.add_argument('--extra', dest='extra', action='store_true',
                        help='allow extra uvicorn args')

    if argv:
        return parser.parse_known_args(argv)
    return parser.parse_known_args()


def run_local(argv=None):
    """ Run a localhost version of the API"""
    known_args, extra_args = arg_parse(argv)
    executable = which('uvicorn')
    exec_args = [f'{executable}', 'zerospeech.api:app']

    if known_args.reload:
        exec_args.append('--reload')

    if known_args.debug:
        exec_args.append('--debug')

    if known_args.extra and extra_args:
        exec_args.extend(extra_args)

    execv(executable, exec_args)
