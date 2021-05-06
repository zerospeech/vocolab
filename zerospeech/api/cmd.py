import argparse
import sys
from os import execv
from shutil import which


def run_local():
    """ Run a localhost version of the API"""
    args = sys.argv[1:]
    executable = which('uvicorn')
    exec_args = [f'{executable}']
    if len(args) == 0:
        exec_args.extend(['zerospeech.api:app', '--reload', '--debug', '--no-access-log'])
    else:
        exec_args.extend(args)

    execv(executable, exec_args)
