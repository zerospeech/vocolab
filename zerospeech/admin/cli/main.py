import argparse
import sys
from argparse import RawTextHelpFormatter

from zerospeech.admin.cli import cmd_types


class AdminCMD:
    __command_list__ = {}

    @staticmethod
    def add_cmd(cmd):
        AdminCMD.__command_list__[cmd.name] = cmd

    def cmd_help(self):
        help_msg = "list of available commands : \n\n"
        for name, cmd in self.__command_list__.items():
            help_msg += f"{cmd.help}\n"
        return help_msg

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Zerospeech Back-end administration tool',
            usage='zr <command> [<args>]',
            epilog=f"{self.cmd_help()}",
            formatter_class=RawTextHelpFormatter
        )
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        actual_cmd, rec_cmd = cmd_types.cmd_parser(args.command)
        cmd_obj = self.__command_list__.get(actual_cmd, None)
        if cmd_obj is None:
            print(f'Unrecognized command {actual_cmd}\n')
            parser.print_help()
            exit(1)

        if cmd_obj.is_cmd():
            cmd_obj.run(sys.argv[2:])
        else:
            cmd_obj.run(rec_cmd, sys.argv[2:])


def run_cli():
    from zerospeech.admin.cli.user import get as get_user_cmd
    from zerospeech.admin.cli.challenges import get as get_ch_cmd
    from zerospeech.admin.cli.checks import get as get_checks
    from zerospeech.admin.cli.submissions import get as get_subs

    # add subcommands
    AdminCMD.add_cmd(get_user_cmd())
    AdminCMD.add_cmd(get_ch_cmd())
    AdminCMD.add_cmd(get_checks())
    AdminCMD.add_cmd(get_subs())

    # run
    AdminCMD()
