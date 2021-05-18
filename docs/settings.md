# Zerospeech-Admin Settings & Config

All settings for the `zerospeech-admin` module are loaded from the [zerospeech.settings](../zerospeech/settings.py) submodule. 

Settings are loaded using [Pydantic](https://pydantic-docs.helpmanual.io/usage/settings/) settings functionalities. 

## Using settings 

From python

```python
from zerospeech import get_settings

_settings = get_settings()

print(_settings.app_name)
```

From cli: `zr check:settings --get <VAR_NAME>`


## Overwrite settings externally

To overwrite the default value of the settings you need to define it as an environment variable using the 
prefix defined for the module `ZR_<VAR_NAME>`.

ex: `> export ZR_API_BASE_URL="http://localhost:8000"`

To define multiple variables easier a `.env` file can be used. 

To load your `.env` file you need to define the following variable `ZR_ENV_FILE` to point to your file.

ex: `export ZR_ENV_FILE=example.env`

The loading order of values is : class defaults, .env file, environment variables

## Values needed for the API

- API_BASE_URL: the url on which the api can be accessed externally.

- **DATA_FOLDER**: directory to write all local data (must exist and be writable)

- TASK QUEUE CONNECTION INFO:  see [pika tutorial](https://www.rabbitmq.com/tutorials/tutorial-one-python.html) for more info on queue connection.

    Values: RPC_USERNAME, RPC_PASSWORD, RPC_HOST, RPC_PORT

- Email Settings : settings to allow email sending.
  
    Values: MAIL_USERNAME, MAIL_PASSWORD, MAIL_SERVER, MAIL_PORT

- Mattermost Settings: info on how to notify activity on mattermost

    Values: MATTERMOST_API_KEY

- REMOTE SETTINGS: information on host(s) that will handle evaluations

    + REMOTE_HOST: a list of the available hosts
    
    + REMOTE_STORAGE: a list of the hosts with their respective storage location
    
    + REMOTE_BIN: a list of the hosts with their respective evaluation script location
    

## Values needed for the Worker


- **DATA_FOLDER**: directory to write all local data (must exist and be writable)

- REMOTE SETTINGS: information on host(s) that will handle evaluations

    + REMOTE_HOST: a list of the available hosts
    
    + REMOTE_STORAGE: a list of the hosts with their respective storage location
    
    + REMOTE_BIN: a list of the hosts with their respective evaluation script location
  


## Settings List

> Any value marked as REQUIRED is needed to be provided at runtime and depends on the environment or contains 
> credentials. If a required setting is not provided correctly some features will not work correctly.

- app_name<str>: The application name, used for labels  (default: Zerospeech Challenge API)
- app_home<DirectoryPath>: The location of the zerospeech module (default: Path(__file__).parent)
- version<str>: A label of the current version of the API, used for documentation & labels (default: v0.1)
- maintainers<str>: The organisation/person maintaining this module (default: CoML Team, INRIA, ENS, EHESS, CNRS)
- admin_email<EmailStr>: The contact email (default: EmailStr("contact@zerospeech.com"))
- hostname<str>: The current machine hostname (default: platform.node())
- DATA_FOLDER<DirectoryPath>: The main application folder of the module  (default:  \*\***REQUIRED**\*\*)
- API_BASE_URL<str>: The base url entrypoint of the API (default: https://api.zerospeech.com)
- db_file<str>: The filename of the sqlite database (default: zerospeech.db)
- doc_title<str>: The main title of the API documentation page (default: Zerospeech Challenge API)
- doc_version<str>: The version of the documentation of the API (default: v0)
- doc_description<str>: A brief description section in the API documentation (default: A documentation of the API for the Zerospeech Challenge back-end !)
- DEBUG<bool> Allow debug information in logs & outputs (default: True)
- COLORS<bool>: Allow colors in logging output (default: True)
- QUIET<bool>: Mute all output logs  (default: False)
- VERBOSE<bool>: Allow debug information in logs (default: False)
- ALLOW_PRINTS<bool>: Allow prints in logs (default: True)
- ROTATING_LOGS<bool>: Use a rotating log fileHandler [requires LOG_FILE to be set] (default: True)
- LOG_FILE<Optional[Path]>: Location to output logs, if None logs are printed in the console (default: None)
- ERROR_LOG_FILE<Optional[Path]>: Location to output error logs, if None error logs are printed in the console (default: None)
- RPC_USERNAME<str>: The username used to login in the RabbitMQ task queue. (default: \*\***REQUIRED**\*\)
- RPC_PASSWORD<str>: The password used to login in the RabbitMQ task queue. (default: \*\***REQUIRED**\*\)
- RPC_HOST<Union[IPvAnyNetwork, str]>: the Hostname/url of the host of the RabbitMQ task queue. (default: \*\***REQUIRED**\*\)
- RPC_PORT<int>: The default port of the RabbitMQ task queue. (default: 5672) 
- HOSTS<Set[str]>: A list of the accessible hosts (hostname or ip) (default: [])
- REMOTE_STORAGE<Dict[str, Path]>: A dictionary containing a mapping between host & storage location 
  used for storing submissions. (default: {} \*\***REQUIRED**\*\)
- REMOTE_BIN<Dict[str, Path]>: A dictionary containing a mapping between hosts and evaluation script locations.
  (default: {} \*\***REQUIRED**\*\)
- favicon<str>: Location of the Favicon to use for the html pages (singup, documentation, etc.)
  (default: http://zerospeech.com/_static/favicon.ico)
- origins<List[str]> A list of allowed cross origins. (default: *zerospeech.com, localhost)
- session_expiry_delay<timedelta>: Delay for log in token to expire. (default: timedelta(days=7))
- password_reset_expiry_delay<timedelta>: Delay for a password reset session to expire. (default: timedelta(minutes=45))
- STATIC_DIR<Path>: The location for static data [<api-url>/static/<path>]. (default: <DATA_FOLDER>/_static)
- USER_DATA_DIR<Path>: The location for user data.  (default: <DATA_FOLDER>/user_data)
- SUBMISSION_DIR<Path>: The location for submission data. (default: <DATA_FOLDER>/submissions)
- TEMPLATES_DIR<Path>: The location for templates [jinja2]. (default: <app_home>/templates)
- HTML_TEMPLATE_DIR<Path>: The location of html page templates. (default:  <TEMPLATES_DIR>/pages)
- MATTERMOST_TEMPLATE_DIR<Path>: The location of mattermost notification templates. (default: <TEMPLATES_DIR>/mattermost)
- mattermost_url<HttpUrl>: Location of the mattermost instance to notify. (default: https://mattermost.cognitive-ml.fr/hooks)
- mattermost_username<str>: Username to use for mattermost notifications. (default: AdminBot)
- mattermost_channel<str>: Mattermost channel to use for notification diffusion. (default: zerospeech)
- MATTERMOST_API_KEY<str>: API key to access the mattermost instance. (default:  \*\***REQUIRED**\*\)
- MAIL_USERNAME<Union[EmailStr, str]>: Username to access SMTP server for email notifications. (default:  \*\***REQUIRED**\*\)
- MAIL_PASSWORD<str>: Password to access SMTP server for email notifications. (default:  \*\***REQUIRED**\*\)
- MAIL_FROM<Union[EmailStr, str]>: Email that users see when they receive notifications. (default:  \*\***REQUIRED**\*\)
- MAIL_FROM_NAME<str>: Person that users see as sender when receiving notifications. (default:  \*\***REQUIRED**\*\)
- MAIL_PORT<int>: Port used to access SMTP server. (default:  587)
- MAIL_SERVER<str>: URL or IP to SMTP server location. (default:  \*\***REQUIRED**\*\)
- MAIL_TLS<bool>: Flag turning on/off TLS SMTP connection. (default: True)
- MAIL_SSL<bool>: FLag turning on/off SSL for SMTP connection. (default: False)
- MAIL_TEMPLATE_DIR<Path>: Location where email templates are stored. (default: <TEMPLATES_DIR>/emails)