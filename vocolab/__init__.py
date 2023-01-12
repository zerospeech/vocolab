from importlib.metadata import version, PackageNotFoundError
from vocolab.settings import get_settings
from vocolab import __out__

try:
    __version__ = version("vocolab")
except PackageNotFoundError:
    # package is not installed
    __version__ = None


class out: # noqa: allow lower case class here
    console: __out__.Console = __out__.Console()
    cli: __out__.Console = __out__.Console(cli=True)
    log: __out__.Log = __out__.Log()
