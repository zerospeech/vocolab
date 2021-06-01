import asyncio
from pathlib import Path

from rich.table import Table

from zerospeech import out
from zerospeech.admin import cmd_lib
from zerospeech.db.q import leaderboard as q_leaderboard
from zerospeech.utils import submissions


class LeaderboardCMD(cmd_lib.CMD):
    """ Administrate Leaderboard entries (default: list)"""

    def __init__(self, root, name, cmd_path):
        super(LeaderboardCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        leaderboards = asyncio.run(q_leaderboard.list_leaderboards())

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column('ID')
        table.add_column('Label')
        table.add_column('Archived')
        table.add_column('External Entries')
        table.add_column('Static Files')
        table.add_column('Challenge ID')
        table.add_column('EntryFile')
        table.add_column('LeaderboardFile')

        for entry in leaderboards:
            table.add_row(
                f"{entry.id}", f"{entry.label}", f"{entry.archived}",
                f"{entry.external_entries}", f"{entry.static_files}", f"{entry.challenge_id}",
                f"{entry.entry_file}", f"{entry.path_to}"
            )


class CreateLeaderboardCMD(cmd_lib.CMD):
    """ Create a new leaderboard entry """

    def __init__(self, root, name, cmd_path):
        super(CreateLeaderboardCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)


class EditLeaderboardCMD(cmd_lib.CMD):
    """ Edit Leaderboard entries """

    def __init__(self, root, name, cmd_path):
        super(EditLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("leaderboard_id", type=int, help='The id of the entry')
        self.parser.add_argument("field_name", type=str, help="The name of the field")
        self.parser.add_argument('field_value', help="The new value of the field")

    def run(self, argv):
        """Edit a field of a leaderboard entry.    """
        _ = self.parser.parse_args(argv)
        self.parser.print_help()


class UpdateExternalEntriesCMD(cmd_lib.CMD):
    """ Update external entries location """

    def __init__(self, root, name, cmd_path):
        super(UpdateExternalEntriesCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument("leaderboard_id", type=int)
        self.parser.add_argument("location", type=Path)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        ...


class ShowLeaderboardCMD(cmd_lib.CMD):
    """ Print final leaderboard object """
    
    def __init__(self, root, name, cmd_path):
        super(ShowLeaderboardCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('leaderboard_id', type=int)

    def run(self, argv):
        args = self.parser.parse_args(argv)
        leaderboard = asyncio.run(submissions.get_leaderboard(leaderboard_id=args.leaderboard_id))
        out.Console.console.print(leaderboard)
    

class BuildLeaderboardCMD:
    pass
