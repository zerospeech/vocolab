import argparse
import sys
from abc import ABC, abstractmethod
from typing import List


def cmd_parser(cmd):
    cmd_split = cmd.split(':')
    actual_cmd = cmd_split[0]
    rec_cmd = ":".join(cmd_split[1:])
    return actual_cmd, rec_cmd


class CMD(ABC):

    def __init__(self, cmd_path):
        self.parser = argparse.ArgumentParser(
            prog=f"{cmd_path}:{self.name}",
            description=self.short_description
        )
        self.cmd_path = cmd_path

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def short_description(self):
        return self.__doc__

    @abstractmethod
    def run(self, argv):
        pass

    @staticmethod
    def is_cmd():
        return True


class CommandCollection(ABC):
    __cmd_list__ = {}

    def __init__(self, parser=None):
        if parser is None:
            self.parser = argparse.ArgumentParser(
                usage=f"{self.name} [args]"
            )
        else:
            self.parser = parser

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def help(self) -> str:
        help_msg = f"{self.name}:\n\n"
        for name, cmd in self.__cmd_list__.items():
            help_msg += f"{self.name}:{name}\t{cmd.short_description}\n"
        return help_msg

    @property
    def description(self) -> str:
        return self.__doc__

    def root_cmd(self, argv):
        print(f"cmd: {self.name}")
        print(f"\t{self.description}")
        print(f"usage: {self.name}:CMD [args]")
        print('SUB-COMMANDS:')
        for name, cmd in self.__cmd_list__.items():
            print(f"\t{name}\t{cmd.short_description}\n")

    def run(self, cmd, argv):
        """ Run a sub-command or a sub-collection from list """
        if cmd == "":
            return self.root_cmd(argv)

        actual_cmd, rec_cmd = cmd_parser(cmd)

        cmd_obj = self.__cmd_list__.get(actual_cmd, None)
        if cmd_obj is None:
            print(f'Command {actual_cmd} not found in collection {self.name}')
            sys.exit(1)

        if rec_cmd:
            return cmd_obj.run(rec_cmd, argv)
        else:
            return cmd_obj.run(argv)

    def add_cmd(self, cmd: CMD):
        self.__cmd_list__[cmd.name] = cmd

    def get_cmd(self, name) -> CMD:
        return self.__cmd_list__.get(name)

    def list(self) -> List[CMD]:
        return list(self.__cmd_list__.values())

    @staticmethod
    def is_cmd():
        return False




