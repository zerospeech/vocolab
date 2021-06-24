import sys
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import logging
from pathlib import Path

from rich.prompt import PromptBase

try:
    import icecream
except ImportError:
    icecream = None

from rich.console import Console as RichConsole
from rich.style import Style
from rich import inspect

from zerospeech.settings import get_settings

ERROR_STYLE = Style(color='red', bold=True, underline=True)
INFO_STYLE = Style(color='green', bold=True)
DEBUG_STYLE = Style(color='yellow', bold=True)
WARNING_STYLE = Style(color='orange1', bold=True)


class PathPrompt(PromptBase[Path]):
    """A prompt that returns an integer.
    Example:
        >>> burrito_count = PathPrompt.ask("Where did you store the treasure ?")
    """

    response_type = Path
    validate_error_message = "[prompt.invalid]Please enter a valid path"


def _get_ic(debug):
    if icecream and debug:
        return icecream.ic
    else:
        return lambda *f: None


# noinspection PyUnresolvedReferences
class MyRotatingFileHandler(RotatingFileHandler):
    """ An overwrite of the default RotationFileHandler to match rich Console API"""
    __record_factory = logging.getLogRecordFactory()

    def record_factory(self, msg):
        return self.__record_factory(
            "fake_bitch",
            1,
            __file__,
            20,
            msg,
            args=[],
            exc_info=None
        )

    def write(self, obj):
        if self.shouldRollover(record=self.record_factory(obj)):
            self.doRollover()
        self.stream.write(obj)


# noinspection PyUnresolvedReferences
class MyWatchedFileHandler(WatchedFileHandler):
    """ An overwrite of the default Watched FileHandler to match rich Console API"""

    def write(self, obj):
        self.reopenIfNeeded()
        self.stream.write(obj)


def build_file_handler(file, should_rotate):
    if should_rotate:
        max_bytes = 536870912  # 500MB
        return MyRotatingFileHandler(file, mode='a', encoding='utf-8', maxBytes=max_bytes, backupCount=5)
    else:
        return MyWatchedFileHandler(file, mode="a", encoding="utf-8")


class _Log:
    """ Internal Class that handles logging functionality """

    def __init__(self, *, neutral_console, info_console, error_console, debug_console, warning_console, verbose):
        self._neutral_console = neutral_console
        self._info_console = info_console
        self._debug_console = debug_console
        self._error_console = error_console
        self._warning_console = warning_console
        self.verbose = verbose

    def log(self, *args, **kwargs):
        self._neutral_console.log(*args, **kwargs)

    def info(self, msg):
        self._info_console.log(f"[INFO] {msg}")

    def debug(self, msg):
        if self.verbose:
            self._debug_console(f"[DEBUG] {msg}")

    def warning(self, msg):
        self._warning_console.log(f"[WARN] {msg}")

    def error(self, msg):
        self._error_console.log(f"[ERROR] {msg}")

    def exception(self, msg=None):
        # backup style
        save_style = self._error_console.style
        self._error_console.style = None

        if msg:
            self._error_console.log(f'{msg}', style="red bold")
        else:
            self._error_console.log('an error has interrupted the current process : ',
                                    style="red bold")
        self._error_console.print_exception(show_locals=self.verbose)

        # restore style
        self._error_console.style = save_style


class _Console:
    """ Console class to handle all types of outputs """

    class _ConfigObject:
        """ Object that holds Console configurations """

        def __init__(self):
            _settings = get_settings()
            self.VERBOSE = _settings.VERBOSE
            self.ROTATING_LOGS = _settings.ROTATING_LOGS
            self.LOG_FILE = _settings.LOG_FILE
            self.ERROR_LOG_FILE = _settings.ERROR_LOG_FILE
            self.ALLOW_PRINTS = _settings.ALLOW_PRINTS
            self.QUIET = _settings.QUIET
            self.DEBUG = _settings.DEBUG
            self.COLORS = _settings.COLORS

    def __init__(self):
        self._config = self._ConfigObject()
        self._info_console = None
        self._debug_console = None
        self._neutral_console = None
        self._error_console = None
        self._warning_console = None
        self.ic = None
        self.inspect = None
        self._logger = None
        self.build_consoles()
        self.PathPrompt = PathPrompt()
        self._logger = _Log(
            neutral_console=self._neutral_console,
            info_console=self._info_console,
            debug_console=self._debug_console,
            warning_console=self._warning_console,
            error_console=self._error_console,
            verbose=self.verbose
        )

    def build_consoles(self):
        """ Build the consoles to output """
        console_options = dict(
            quiet=self.quiet,
            no_color=not self.has_colors,
        )

        if self.log_to_file:
            console_options["file"] = build_file_handler(self._config.LOG_FILE, self._config.ROTATING_LOGS)

        self._info_console = RichConsole(**console_options, style=INFO_STYLE)
        self._debug_console = RichConsole(**console_options, style=DEBUG_STYLE)
        self._neutral_console = RichConsole(**console_options)

        if self.error_to_file:
            console_options["file"] = build_file_handler(self._config.ERROR_LOG_FILE, self._config.ROTATING_LOGS)

        self._error_console = RichConsole(**console_options, stderr=True, style=ERROR_STYLE)
        self._warning_console = RichConsole(**console_options, stderr=True, style=WARNING_STYLE)

        self.ic = _get_ic(self.is_debug)
        if self.is_debug:
            self.inspect = inspect
        else:
            self.inspect = lambda *f: None

    # noinspection PyPep8Naming
    @property
    def Logger(self) -> '_Log':
        return self._logger

    @property
    def verbose(self):
        return self._config.VERBOSE

    @verbose.setter
    def verbose(self, value: bool):
        self._config.VERBOSE = value

    @property
    def log_to_file(self):
        return self._config.LOG_FILE is not None

    @property
    def error_to_file(self):
        return self._config.ERROR_LOG_FILE is not None

    @property
    def allow_prints(self):
        return self._config.ALLOW_PRINTS

    @allow_prints.setter
    def allow_prints(self, value: bool):
        self._config.ALLOW_PRINTS = value
        if value:
            self._config.LOG_FILE = None
            self._config.ERROR_LOG_FILE = None
            self.build_consoles()

    @property
    def quiet(self):
        return self._config.QUIET

    @quiet.setter
    def quiet(self, value: bool):
        self._config.QUIET = value

    @property
    def is_debug(self):
        return self._config.DEBUG

    @property
    def has_colors(self):
        return self._config.COLORS

    @has_colors.setter
    def has_colors(self, value: bool):
        self._config.COLORS = value

    @property
    def console(self) -> RichConsole:
        return self._neutral_console

    def info(self, *args, **kwargs):
        # print not allowed when logging to files
        if self.allow_prints and not self.log_to_file:
            self._info_console.print(*args, **kwargs)

    def debug(self, *args, **kwargs):
        # print not allowed when logging to files
        if self.allow_prints and not self.log_to_file and self.verbose:
            self._debug_console.print(*args, **kwargs)

    def warning(self, *args, **kwargs):
        # print not allowed when logging to files
        if self.allow_prints and not self.error_to_file:
            return self._warning_console.print(*args, **kwargs)

    def error(self, *args, **kwargs):
        # print not allowed when logging to files
        if self.allow_prints and not self.error_to_file:
            return self._error_console.print(*args, **kwargs)

    def exception(self):
        # print not allowed when logging to files
        if self.allow_prints and not self.error_to_file:
            self._neutral_console.print_exception()

    def print(self, *args, **kwargs):
        # print not allowed when logging to files
        if self.allow_prints:
            return self._neutral_console.print(*args, **kwargs)


# Instantiate Console
# noinspection PyTypeChecker
sys.modules[__name__] = _Console()
