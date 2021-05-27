import sys

from rich.console import Console
from rich.markdown import Markdown

from zerospeech import get_settings
from zerospeech.admin import cmd_lib

_settings = get_settings()
console = Console()

settings_info_md = """
## Zerospeech - Admin Settings - Info

> **Settings:** are imported using the following pattern : 

```python
from zerospeech import get_settings

_settings = get_settings()
```

> **Loading:** settings are loaded from the `Settings` class in `zerospeech.settings` module

> **Overwriting:** to overwrite a value you need to set an environmental value before the setting are loaded.

**Prefix** all values need to have this prefix outside of the Settings class : `ZR_<varname>`

ex: `export ZR_app_name=my_test_app`

> **Loading from env file:** to load a set of values from an .env file you need to set the `ZR_ENV_FILE` to point to your file.

For examples of .env files see `example.env` 

For more information on all the variables & their usage see [docs folder](docs/settings.md)
"""


class ChecksCMD(cmd_lib.CMD):
    """ A container for check commands """
    
    def __init__(self, root, name, cmd_path):
        super(ChecksCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        self.parser.print_help()
        sys.exit(0)


class CheckSettingsCMD(cmd_lib.CMD):
    """ Command allowing to verify settings """

    def __init__(self, root, name, cmd_path):
        super(CheckSettingsCMD, self).__init__(root, name, cmd_path)
        # arguments
        self.parser.add_argument('--get', help='Retrieves a specific value')
        self.parser.add_argument('--info', help='Info on how to set settings', action='store_true')
        self.parser.add_argument('--keys', help='List all available keys', action='store_true')

    def run(self, argv):
        args = self.parser.parse_args(argv)

        if args.get:
            try:
                v = _settings.__getattribute__(args.get)
                console.print(f"[green]{v}[/green]")
            except AttributeError:
                console.print(f":x: Key {args.get} not found", style='red bold')

        elif args.keys:
            console.print([i for i in _settings.__fields__ if i != 'local'])
        elif args.info:
            md = Markdown(settings_info_md)
            console.print(md)
        else:
            console.print("---------------- Zerospeech API Settings ----------------",
                          style="bold italic purple")
            for i in _settings.__fields__:
                if i == 'local':
                    continue
                console.print(f"[red][bold]{i}[/bold][/red] => [blue]{_settings.__getattribute__(i)}[/blue]")
            console.print("---------------- Zerospeech API Settings ----------------",
                          style="bold italic purple")

            console.print("---------------------------------------------------------",
                          style="bold italic purple")

