import argparse
import sys
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Optional

from treelib import Tree, Node

from zerospeech import out


class CMD(ABC):

    def __init__(self, root, name, cmd_path):
        self._unique_id = f"{uuid.uuid4()}"
        self.cmd_path = cmd_path
        self._name = name

        prog = f"{root} {cmd_path}:{name}"
        if cmd_path == '':
            prog = f"{root} {name}"

        self.parser = argparse.ArgumentParser(
            prog=prog,
            description=self.short_description,
            formatter_class=argparse.RawTextHelpFormatter
        )

    @property
    def short_description(self):
        return self.__doc__

    @property
    def label(self):
        return f"{self._name}:\t{self.short_description}"

    def add_epilog(self, child_info):
        # todo check if this works
        self.parser.epilog = child_info

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._unique_id

    @abstractmethod
    def run(self, argv):
        pass


class CommandTree:
    __RootNodeLabel = namedtuple('__RootNodeLabel', 'label')

    def __init__(self):
        self.__cmd_tree = Tree()
        self.__cmd_tree.create_node('.', 0, data=self.__RootNodeLabel(label='.'))

    def find_cmd(self, path: str) -> Optional[Node]:
        current_node = 0
        for tag in path.split(':'):
            if current_node is None: return None
            current_node = next((x.identifier for x in self.__cmd_tree.children(current_node) if x.tag == tag), None)
        return self.__cmd_tree.get_node(current_node)

    def add_cmd(self, cmd: CMD):
        father_node = self.find_cmd(cmd.cmd_path)
        if father_node is None:
            father_node = self.__cmd_tree.get_node(self.__cmd_tree.root)

        self.__cmd_tree.create_node(
            tag=f"{cmd.name}",
            identifier=cmd.id,
            data=cmd,
            parent=father_node.identifier
        )

    def has_children(self, _id):
        return self.__cmd_tree.children(_id)

    def show(self, root=None) -> str:
        if root:
            return self.__cmd_tree.subtree(root).show(data_property="label", stdout=False)
        else:
            return self.__cmd_tree.show(data_property="label", stdout=False)

    def build_epilogs(self):
        """ Iterate over all nodes and append epilog to help message"""
        for node in self.__cmd_tree.all_nodes():
            if node.identifier == 0:
                continue
            if not self.has_children(node.identifier):
                continue

            epilog = "---\n" \
                     "list of available commands : \n\n" \
                     f"{self.show(root=node.identifier)}"
            node.data.add_epilog(epilog)


class CLI:
    """ The Command Line Interface Builder Class """
    __help_commands = ['help', 'list', 'commands']

    def is_help_cmd(self, cmd):
        return cmd in self.__help_commands

    def __init__(self, cmd_tree: CommandTree, *,
                 description: str = "",
                 usage: str = "",
                 ):
        """

        :param cmd_tree:
        :param description:
        :param usage:
        """

        # Help epilog
        epilog = "---\n" \
                 "list of available commands : \n\n" \
                 f"{cmd_tree.show()}"

        parser = argparse.ArgumentParser(
            description=description,
            usage=usage,
            epilog=epilog,
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        # check if help is asked
        if self.is_help_cmd(args.command):
            parser.print_help()
            sys.exit(0)

        cmd_node = cmd_tree.find_cmd(args.command)
        if cmd_node is None or cmd_node.identifier == 0:
            out.Console.error(f'Unrecognized command {args.command}\n')
            parser.print_help()
            sys.exit(1)

        cmd = cmd_node.data
        if not isinstance(cmd, CMD):
            out.Console.error(f'Unrecognized command {args.command}\n')
            parser.print_help()
            sys.exit(2)
        # set current cmd
        self.cmd = cmd

    def run(self):
        self.cmd.run(argv=sys.argv[2:])
