from zerospeech import get_settings
from zerospeech.admin import cmd_lib, commands

# settings
_settings = get_settings()
has_db = (_settings.DATA_FOLDER / _settings.db_file).is_file()
has_users = has_db and _settings.USER_DATA_DIR.is_dir()
has_challenges = has_db
has_submissions = _settings.SUBMISSION_DIR.is_dir()
CMD_NAME = "zr"


def build_cli():
    tree = cmd_lib.CommandTree()

    if has_users:
        # user functions
        tree.add_cmd(
            commands.user.UsersCMD(CMD_NAME, 'users', '')
        )
        tree.add_cmd(
            commands.user.LoggedUsersCMD(CMD_NAME, 'logged', 'users')
        )
        tree.add_cmd(
            commands.user.CreateUserCMD(CMD_NAME, 'create', 'users')
        )
        tree.add_cmd(
            commands.user.VerifyUserCMD(CMD_NAME, 'verify', 'users')
        )
        tree.add_cmd(
            commands.user.UserActivationCMD(CMD_NAME, 'activate', 'users')
        )
        tree.add_cmd(
            commands.user.PasswordUserCMD(CMD_NAME, 'password', 'users')
        )

    if has_challenges:
        # challenge functions
        tree.add_cmd(
            commands.challenges.ChallengesCMD(CMD_NAME, 'challenges', '')
        )
        tree.add_cmd(
            commands.challenges.AddChallengeCMD(CMD_NAME, 'add', 'challenges')
        )
        tree.add_cmd(
            commands.challenges.SetChallenge(CMD_NAME, 'set', 'challenges')
        )

    if has_db:
        tree.add_cmd(
            commands.evaluators.EvaluatorsCMD(CMD_NAME, 'evaluators', '')
        )
        tree.add_cmd(
            commands.evaluators.ListRegisteredEvaluatorsCMD(CMD_NAME, 'list', 'evaluators')
        )
        tree.add_cmd(
            commands.evaluators.ListHostsEvaluatorsCMD(CMD_NAME, 'hosts', 'evaluators')
        )
        tree.add_cmd(
            commands.evaluators.DiscoverEvaluatorsCMD(CMD_NAME, 'discover', 'evaluators')
        )

    if has_db and has_submissions:
        tree.add_cmd(
            commands.submissions.SubmissionCMD(CMD_NAME, 'submissions', '')
        )
        tree.add_cmd(
            commands.submissions.SetSubmissionCMD(CMD_NAME, 'set', 'submissions')
        )
        # todo: do we really need a delete function ?
        # tree.add_cmd(
        #     commands.submissions.DeleteSubmissionCMD(CMD_NAME, 'delete', 'submissions')
        # )
        tree.add_cmd(
            commands.submissions.CreateSubmissionCMD(CMD_NAME, 'create', 'submissions')
        )
        tree.add_cmd(
            commands.submissions.EvalSubmissionCMD(CMD_NAME, 'eval', 'submissions')
        )

    tree.add_cmd(
        commands.checks.ChecksCMD(CMD_NAME, 'check', '')
    )
    tree.add_cmd(
        commands.checks.CheckSettingsCMD(CMD_NAME, 'settings', 'check')
    )

    # build all epilog info
    tree.build_epilogs()

    # Build CLI object
    return cmd_lib.CLI(
        tree,
        description="Zerospeech Back-end administration tool",
        usage=f"{CMD_NAME} <command> [<args>]"
    )


def run_cli():
    """ Admin cli Entrypoint """
    cli = build_cli()
    cli.run()
