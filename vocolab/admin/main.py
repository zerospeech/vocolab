import sys

from vocolab import get_settings, out
from vocolab.core import cmd_lib
from vocolab.admin import commands

# settings
_settings = get_settings()
has_db = _settings.database_file.is_file()
has_users = has_db and _settings.user_data_dir.is_dir()
has_challenges = has_db
has_submissions = _settings.submission_dir.is_dir()
has_leaderboard = _settings.leaderboard_dir.is_dir()
is_dev = _settings.console_options.DEBUG is True
CMD_NAME = "voco"


def build_cli():
    tree = cmd_lib.CommandTree()

    if has_users:
        # user functions
        tree.add_cmd_tree(
            commands.user.UsersCMD(CMD_NAME, 'users', ''),
            # commands.user.UserSessionsCMD(CMD_NAME, 'sessions', 'users'),
            # commands.user.CloseUserSessionsCMD(CMD_NAME, 'close', 'users:sessions'),
            commands.user.CreateUserSessionCMD(CMD_NAME, 'create', 'users:sessions'),
            commands.user.CreateUserCMD(CMD_NAME, 'create', 'users'),
            commands.user.VerifyUserCMD(CMD_NAME, 'verify', 'users'),
            commands.user.UserActivationCMD(CMD_NAME, 'activate', 'users'),
            commands.user.PasswordUserCMD(CMD_NAME, 'password', 'users'),
            commands.user.CheckPasswordCMD(CMD_NAME, 'check', 'users:password'),
            # commands.user.ResetSessionsCMD(CMD_NAME, 'reset', 'users:password'),
            commands.user.NotifyCMD(CMD_NAME, 'notify', 'users'),
            commands.user.DeleteUser(CMD_NAME, 'delete', 'users')
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
            commands.submissions.SetSubmissionCMD(CMD_NAME, 'status', 'submissions'),
            commands.submissions.CreateSubmissionCMD(CMD_NAME, 'create', 'submissions'),
            commands.submissions.EvalSubmissionCMD(CMD_NAME, 'eval', 'submissions'),
            commands.submissions.DeleteSubmissionCMD(CMD_NAME, 'delete', 'submissions'),
            commands.submissions.FetchSubmissionFromRemote(CMD_NAME, 'fetch', 'submissions'),
            commands.submissions.UploadSubmissionToRemote(CMD_NAME, 'upload', 'submissions'),
            commands.submissions.SubmissionSetEvaluator(CMD_NAME, 'evaluator', 'submissions'),
            commands.submissions.SubmissionSetAuthorLabel(CMD_NAME, 'author_label', 'submissions'),
            commands.submissions.ArchiveSubmissionCMD(CMD_NAME, 'archive', 'submissions')
        )

    if has_submissions:
        tree.add_cmd_tree(
            commands.task_worker.TaskWorkerCMD(CMD_NAME, 'worker', ''),
            commands.task_worker.SendEchoMessage(CMD_NAME, 'test_echo', 'worker'),
            commands.task_worker.GenerateWorkerCMD(CMD_NAME, 'generate', 'worker'),
            commands.task_worker.GenerateWorkerSettings(CMD_NAME, 'settings', 'worker:generate'),
            commands.task_worker.GenerateSystemDUnit(CMD_NAME, 'systemD', 'worker:generate'),
            commands.messaging.MessagingCMD(CMD_NAME, 'messaging', ''),
            commands.messaging.UpdateMessageCMD(CMD_NAME, 'update', 'messaging'),
            commands.messaging.EchoMessageCMD(CMD_NAME, 'echo', 'messaging')
        )

    tree.add_cmd_tree(
        commands.settings.SettingsCMD(CMD_NAME, 'settings', ''),
        commands.settings.GenerateEnvFileCMD(CMD_NAME, 'template', 'settings'),
        commands.api.APICMD(CMD_NAME, 'api', ''),
        commands.api.DebugAPICMD(CMD_NAME, 'serve', 'api'),
        commands.api.APInitEnvironmentCMD(CMD_NAME, 'init', 'api'),
        commands.api.ConfigFiles(CMD_NAME, 'config', 'api'),
        commands.api.GunicornConfigGeneration(CMD_NAME, 'gunicorn', 'api:config'),
        commands.api.SystemDSocketFileGeneration(CMD_NAME, 'socket', 'api:config'),
        commands.api.SystemDUnitGeneration(CMD_NAME, 'service', 'api:config'),
        commands.api.NginxConfigGeneration(CMD_NAME, 'nginx', 'api:config')
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
        commands.test.TestEmail(CMD_NAME, 'email', 'test')
    )

    if is_dev:
        tree.add_cmd_tree(
            commands.test.TestDebugCMD(CMD_NAME, 'debug', 'test')
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
    try:
        cli = build_cli()
        cli.run()
    except Exception: # noqa: broad thing allows for prettyprinting
        out.cli.exception()  # cli pretty prints exceptions
        sys.exit(1)
