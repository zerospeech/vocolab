from zerospeech import get_settings
from zerospeech.admin import cmd_lib, commands

# settings
_settings = get_settings()
has_db = (_settings.DATA_FOLDER / _settings.db_file).is_file()
has_users = has_db and _settings.USER_DATA_DIR.is_dir()
has_challenges = has_db
has_submissions = _settings.SUBMISSION_DIR.is_dir()
has_leaderboard = _settings.LEADERBOARD_LOCATION.is_dir()
CMD_NAME = "zr"


def build_cli():
    tree = cmd_lib.CommandTree()

    if has_users:
        # user functions
        tree.add_cmd_tree(
            commands.user.UsersCMD(CMD_NAME, 'users', ''),
            commands.user.UserSessionsCMD(CMD_NAME, 'sessions', 'users'),
            commands.user.CloseUserSessionsCMD(CMD_NAME, 'close', 'users:sessions'),
            commands.user.CreateUserSessionsCMD(CMD_NAME, 'create', 'users:sessions'),
            commands.user.CreateUserCMD(CMD_NAME, 'create', 'users'),
            commands.user.VerifyUserCMD(CMD_NAME, 'verify', 'users'),
            commands.user.UserActivationCMD(CMD_NAME, 'activate', 'users'),
            commands.user.PasswordUserCMD(CMD_NAME, 'password', 'users')
        )

    if has_challenges:
        # challenge functions
        tree.add_cmd_tree(
            commands.challenges.ChallengesCMD(CMD_NAME, 'challenges', ''),
            commands.challenges.AddChallengeCMD(CMD_NAME, 'add', 'challenges'),
            commands.challenges.SetChallenge(CMD_NAME, 'set', 'challenges')
        )

    if has_db:
        tree.add_cmd_tree(
            commands.evaluators.EvaluatorsCMD(CMD_NAME, 'evaluators', ''),
            commands.evaluators.ListHostsEvaluatorsCMD(CMD_NAME, 'hosts', 'evaluators'),
            commands.evaluators.DiscoverEvaluatorsCMD(CMD_NAME, 'discover', 'evaluators'),
            commands.evaluators.UpdateBaseArguments(CMD_NAME, 'args', 'evaluators')
        )

    if has_db and has_submissions:
        tree.add_cmd_tree(
            commands.submissions.SubmissionCMD(CMD_NAME, 'submissions', ''),
            commands.submissions.SetSubmissionCMD(CMD_NAME, 'set', 'submissions'),
            #  todo: do we really need a delete function ?
            #  commands.submissions.DeleteSubmissionCMD(CMD_NAME, 'delete', 'submissions')
            commands.submissions.CreateSubmissionCMD(CMD_NAME, 'create', 'submissions'),
            commands.submissions.EvalSubmissionCMD(CMD_NAME, 'eval', 'submissions')
        )

    if has_submissions:
        tree.add_cmd_tree(
            commands.task_worker.TaskWorkerCMD(CMD_NAME, 'worker', ''),
            commands.task_worker.RunTaskWorkerCMD(CMD_NAME, 'run', 'worker'),
            commands.task_worker.EchoTaskWorkerCMD(CMD_NAME, 'echo', 'worker:run'),
            commands.task_worker.EvaluationTaskWorkerCMD(CMD_NAME, 'eval', 'worker:run'),
            commands.task_worker.UpdateTaskWorkerCMD(CMD_NAME, 'update', 'worker:run')
        )

    tree.add_cmd_tree(
        commands.checks.ChecksCMD(CMD_NAME, 'check', ''),
        commands.checks.CheckSettingsCMD(CMD_NAME, 'settings', 'check'),
        commands.api.APICMD(CMD_NAME, 'api', ''),
        commands.api.DebugAPICMD(CMD_NAME, 'debug', 'api'),
        commands.api.APInitEnvironmentCMD(CMD_NAME, 'init', 'api')
    )

    if has_leaderboard and has_submissions:
        tree.add_cmd_tree(
            commands.leaderboards.LeaderboardCMD(CMD_NAME, 'leaderboards', ''),
            commands.leaderboards.CreateLeaderboardCMD(CMD_NAME, 'create', 'leaderboards'),
            commands.leaderboards.EditLeaderboardCMD(CMD_NAME, 'edit', 'leaderboards'),
            commands.leaderboards.BuildLeaderboardCMD(CMD_NAME, 'build', 'leaderboards'),
            commands.leaderboards.ShowLeaderboardCMD(CMD_NAME, 'show', 'leaderboards')
        )

    tree.add_cmd_tree(
        commands.test.TestCMD(CMD_NAME, 'test', ''),
        commands.test.TestEchoWorker(CMD_NAME, 'echo', 'test'),
        commands.test.TestEmail(CMD_NAME, 'email', 'test')
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
