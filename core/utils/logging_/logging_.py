"""
Contains functions for logging setup.

.. func:: _create_dirs_for_logs(config: dict) -> None
.. func:: setup_logging(config_path: pathlib.Path, default_level: Union[int, str] = logging.INFO) -> None

.. data:: DEFAULT_LOGGING_BASIC_CONFIG
"""

import logging
import logging.config
import pathlib
from typing import (
    Union
)

import yaml


__all__ = ['setup_logging']


logger = logging.getLogger(__name__)


DEFAULT_LOGGING_BASIC_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(thread)d - %(filename)s - %(funcName)s() [%(lineno)s] : %(message)s"
}


def _create_dirs_for_logs(config: dict) -> None:
    """
    Create directories for log files.

    :param config: logging config loaded from .yaml file
    :type config: dict

    :return: None
    :rtype: None
    """

    for handler_name in config['handlers']:
        if 'file' in handler_name:
            log_path = pathlib.Path(config['handlers'][handler_name]['filename'])
            log_dir_path = log_path.parent
            log_dir_path.mkdir(parents=True, exist_ok=True)


def setup_logging(config_path: pathlib.Path, default_level: Union[int, str] = logging.INFO) -> None:
    """
    Setup logging.

    :param config_path: path to yaml file config
    :type config_path: pathlib.Path
    :param default_level: logging level that used if config setting is crashed
    :type default_level: Union[int, str]

    :return: None
    :rtype: None
    """

    DEFAULT_LOGGING_BASIC_CONFIG['level'] = default_level

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as config_file:
            try:
                config = yaml.safe_load(config_file.read())

                _create_dirs_for_logs(config)

                logging.config.dictConfig(config)
            except Exception as error:
                logging.basicConfig(**DEFAULT_LOGGING_BASIC_CONFIG)
                logger.exception(msg='During logging initializing from config file error raised!', exc_info=error)
                logger.info('Default logging config is using!')
            else:
                logger.info('Logging configuration successfully set!')
    else:
        logging.basicConfig(**DEFAULT_LOGGING_BASIC_CONFIG)
        logger.info('During logging initializing failed to load the configuration file. Default config is using!')
