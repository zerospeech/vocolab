import argparse
import sys
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Optional

from treelib import Tree, Node

from vocolab import out

# a function for autocompletion in bash/zsh
BASH_AUTOCOMPLETE_FN = """
# Add The following to your .bashrc / .zshrc
# ------ Zerospeech CLI autocomplete ------
_script()
{
  _script_commands=$(zr __all_cmd__)

  local cur
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(compgen -W "${_script_commands}" -- ${cur}) )

  return 0
}
complete -o default -F _script zr
# ------ Zerospeech CLI autocomplete ------
"""


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
            formatter_class=argparse.RawTextHelpFormatter
        )
        # load description
        if self.long_description:
            self.parser.description = self.long_description
        else:
            self.parser.description = self.short_description

    @property
    def short_description(self):
        return self.__doc__

    @property
    def long_description(self):
        return self.run.__doc__

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
    __help_commands = ['help', 'list', 'commands', '--help', '-h']
    __autocomplete = '__all_cmd__'
    __autocomplete_fn = '__auto_fn__'

    def is_help_cmd(self, cmd):
        return cmd in self.__help_commands

    def is_auto_fn(self, cmd):
        return cmd == self.__autocomplete_fn

    def is_autocomplete(self, cmd):
        return cmd == self.__autocomplete

    def __init__(self):
        self.__cmd_tree = Tree()
        self.__cmd_tree.create_node('.', 0, data=self.__RootNodeLabel(label='.'))

    def find_cmd(self, path: str) -> Optional[Node]:
        current_node = 0
        for tag in path.split(':'):
            if current_node is None:
                return None
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

    def add_cmd_tree(self, *cmd_items):
        for cmd in cmd_items:
            self.add_cmd(cmd)

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
                     "list of available sub-commands : \n\n" \
                     f"{self.show(root=node.identifier)}"
            node.data.add_epilog(epilog)

    def get_all_paths(self):
        paths_as_list = []
        paths_as_str = []
        tree = self.__cmd_tree
        for leaf in tree.all_nodes():
            paths_as_list.append([tree.get_node(nid).tag for nid in tree.rsearch(leaf.identifier)][::-1])

        for item in paths_as_list:
            if '.' in item:
                item.remove('.')
            paths_as_str.append(':'.join(item))

        if '' in paths_as_str:
            paths_as_str.remove('')

        paths_as_str.extend(self.__help_commands)
        paths_as_str.append(self.__autocomplete)
        paths_as_str.append(self.__autocomplete_fn)
        return paths_as_str


class CLI:
    """ The Command Line Interface Builder Class """

    def __init__(self, cmd_tree: CommandTree, *,
                 description: str = "",
                 usage: str = "",
                 ):
        """

        :param cmd_tree:
        :param description:
        :param usage:
        """
        self.cmd_tree = cmd_tree

        # Help epilog
        epilog = "---\n" \
                 "list of available commands : \n\n" \
                 f"{cmd_tree.show()}"

        self.parser = argparse.ArgumentParser(
            description=description,
            usage=usage,
            epilog=epilog,
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.parser.add_argument('command', help='Subcommand to run')

    def run(self):
        """ Run the Command Line Interface """
        args = self.parser.parse_args(sys.argv[1:2])

        # check if help is asked
        if self.cmd_tree.is_help_cmd(args.command):
            self.parser.print_help()
            sys.exit(0)

        # check if requesting cmd list for autocomplete
        if self.cmd_tree.is_autocomplete(args.command):
            # todo add 2 argument for subcommand autocompletion
            out.cli.print(" ".join(self.cmd_tree.get_all_paths()))
            sys.exit(0)

        # check if requesting auto complete bash function
        if self.cmd_tree.is_auto_fn(args.command):
            out.cli.print(BASH_AUTOCOMPLETE_FN)
            sys.exit(0)

        cmd_node = self.cmd_tree.find_cmd(args.command)
        if cmd_node is None or cmd_node.identifier == 0:
            out.cli.error(f'Unrecognized command {args.command}\n')
            self.parser.print_help()
            sys.exit(1)

        cmd = cmd_node.data
        if not isinstance(cmd, CMD):
            out.cli.error(f'Unrecognized command {args.command}\n')
            self.parser.print_help()
            sys.exit(2)

        # call sub-command
        cmd.run(argv=sys.argv[2:])
