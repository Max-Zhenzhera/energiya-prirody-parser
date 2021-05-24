"""
Contains main function.

.. func:: main() -> None
"""


# setup logging for entire project--------------------------------------------------------------------------------------
import logging
from typing import Optional

from .settings import (
    LOGGING_CONFIG_PATH,
    WEBSITE_HOMEPAGE
)
from .utils.logging_ import setup_logging


setup_logging(LOGGING_CONFIG_PATH)
# ----------------------------------------------------------------------------------------------------------------------

from .client import ParserClient


logger = logging.getLogger(__name__)


def main(link: Optional[str] = None, directory: Optional[str] = None, workers: Optional[int] = None) -> None:
    """
    Executable in entry point (__main__.py).

    :param link: link that refers on products group
    :type link: Optional[str]
    :param directory: path to the dump
    :type directory: Optional[str]
    :param workers: quantity of the workers
    :type workers: Optional[int]

    :return: None
    :rtype: None
    """

    if link is None:
        link = WEBSITE_HOMEPAGE

    if workers is None:
        workers = 1

    client: ParserClient
    with ParserClient.manager() as client:
        client.dump_group(
            url=link,
            dir_name=directory,
            max_workers=workers,
        )
