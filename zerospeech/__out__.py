import logging
from logging.handlers import RotatingFileHandler, WatchedFileHandler
from pathlib import Path
from typing import Dict

from rich.prompt import PromptBase

try:
    import icecream
except ImportError:
    icecream = None

from rich.console import Console as RichConsole
from rich.style import Style
from rich import inspect

from zerospeech.settings import get_settings


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


class _out_config_cls:  # noqa: lowercase class as internal objects
    ERROR_STYLE = Style(color='red', bold=True, underline=True)
    INFO_STYLE = Style(color='green', bold=True)
    DEBUG_STYLE = Style(color='yellow', bold=True)
    WARNING_STYLE = Style(color='orange1', bold=True)

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

    @property
    def log_to_file(self):
        return self.LOG_FILE is not None

    @property
    def error_to_file(self):
        return self.ERROR_LOG_FILE is not None

    @property
    def console_options(self) -> Dict:
        return dict(
            quiet=self.QUIET,
            no_color=not self.COLORS,
        )

    @property
    def logger_options(self):
        console_options = dict(
            quiet=self.QUIET,
            no_color=not self.COLORS,
        )

        if self.log_to_file:
            console_options["file"] = build_file_handler(self.LOG_FILE, self.ROTATING_LOGS)

        if self.error_to_file:
            console_options["file"] = build_file_handler(self.ERROR_LOG_FILE, self.ROTATING_LOGS)

        return console_options


def do_nothing(*args, **kwargs): # noqa: unused is the point
    """ a function that does nothing """
    pass


def _get_ic_function():
    """ Return the icecream debug function if it is installed """
    if icecream:
        return icecream.ic
    else:
        return do_nothing


class Console:

    def __init__(self, cli: bool = False):
        cfg = _out_config_cls()

        opts = cfg.console_options
        self._info_console = RichConsole(**opts, style=cfg.INFO_STYLE)
        self._debug_console = RichConsole(**opts, style=cfg.DEBUG_STYLE)
        self._error_console = RichConsole(**opts, stderr=True, style=cfg.ERROR_STYLE)
        self._warning_console = RichConsole(**opts, stderr=True, style=cfg.WARNING_STYLE)
        self._neutral_console = RichConsole(**opts)

        # debug options set to do_nothing by default
        self.ic = do_nothing
        self.inspect = do_nothing

        if cfg.ALLOW_PRINTS is False and cli is False:
            setattr(self, "info", do_nothing)
            setattr(self, "debug", do_nothing)
            setattr(self, "warning", do_nothing)
            setattr(self, "error", do_nothing)

        if cfg.VERBOSE is False:
            setattr(self, "info", do_nothing)

        if cfg.DEBUG is False:
            setattr(self, "debug", do_nothing)
        else:
            setattr(self, "ic", _get_ic_function())
            setattr(self, "inspect", inspect)

    @property
    def raw(self) -> RichConsole:
        return self._neutral_console

    def print(self, *args, **kwargs):
        """ Neutral printing to console """
        self._neutral_console.print(*args, **kwargs)

    def info(self, *args, **kwargs):
        """ Print an informational message to console """
        self._info_console.print(*args, **kwargs)

    def debug(self, *args, **kwargs):
        """ Print a debug message """
        self._debug_console.print(*args, **kwargs)

    def warning(self, *args, **kwargs):
        """ Print a warning message """
        self._warning_console.print(*args, **kwargs)

    def error(self, *args, **kwargs):
        """Print an error message """
        self._error_console.print(*args, **kwargs)

    def exception(self):
        """ PrettyPrint the current raised exception """
        self._neutral_console.print_exception()


class Log:

    def __init__(self):
        cfg = _out_config_cls()

        opts = cfg.logger_options
        self._info_console = RichConsole(**opts, style=cfg.INFO_STYLE)
        self._debug_console = RichConsole(**opts, style=cfg.DEBUG_STYLE)
        self._error_console = RichConsole(**opts, stderr=True, style=cfg.ERROR_STYLE)
        self._warning_console = RichConsole(**opts, stderr=True, style=cfg.WARNING_STYLE)
        self._neutral_console = RichConsole(**opts)
        self.verbose = cfg.VERBOSE

        if cfg.VERBOSE is False:
            setattr(self, "log", do_nothing)
            setattr(self, "info", do_nothing)
            setattr(self, "debug", do_nothing)

        if cfg.DEBUG is False:
            setattr(self, "debug", do_nothing)

    @property
    def raw(self) -> RichConsole:
        return self._neutral_console

    def log(self, *args, **kwargs):
        """ Write into the log """
        self._neutral_console.log(*args, **kwargs)

    def info(self, msg):
        """ Log an info message """
        self._info_console.log(f"[INFO] {msg}")

    def debug(self, msg):
        """ Log a debug message """
        self._debug_console.log(f"[DEBUG] {msg}")

    def warning(self, msg):
        """ Log a warning message """
        self._warning_console.log(f"[WARN] {msg}")

    def error(self, msg):
        """ Log an error message """
        self._error_console.log(f"[ERROR] {msg}")

    def exception(self, msg=None):
        """ Log an exception """
        if msg:
            self._neutral_console.log(f'{msg}', style="red bold")
        else:
            self._neutral_console.log('an error has interrupted the current process : ',
                                      style="red bold")
        self._neutral_console.print_exception(show_locals=self.verbose)

