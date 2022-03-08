from zerospeech.settings import get_settings
from zerospeech import __out__

class out: # noqa: allow lower case class here
    console: __out__.Console = __out__.Console()
    cli: __out__.Console = __out__.Console(cli=True)
    log: __out__.Log = __out__.Log()
