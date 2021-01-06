import logging
from logging import Logger, getLogger
from logging.handlers import RotatingFileHandler


from zerospeech.settings import get_settings

_settings = get_settings()


class LogSingleton:
    """ Singleton Log Getter/Setter"""
    __instance: Logger = None

    @staticmethod
    def get():
        if LogSingleton.__instance is None:
            LogSingleton.__instance = getLogger(__name__)
        return LogSingleton.__instance

    @staticmethod
    def set_level(level):
        if LogSingleton.__instance is None:
            LogSingleton.__instance = getLogger(__name__)
        LogSingleton.__instance.setLevel(level)


if _settings.LOGGER_TYPE is 'file':
    # File Configuration
    logging.basicConfig(level=_settings.LOG_LEVEL,
                        format='[%(asctime)s] %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=str(_settings.LOG_FILE),
                        filemode='w'
                        )
else:
    # Console configuration
    logging.basicConfig(
        level=_settings.LOG_LEVEL,
        format='[%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',

    )


LogSingleton.set_level(_settings.LOG_LEVEL)
