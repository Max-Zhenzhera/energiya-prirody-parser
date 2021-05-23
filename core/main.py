"""
Contains main function.

.. func:: main() -> None
"""

# setup logging for entire project--------------------------------------------------------------------------------------
import logging

from .settings import (
    LOGGING_CONFIG_PATH,
    WEBSITE_HOMEPAGE
)
from .utils.logging_ import setup_logging


setup_logging(LOGGING_CONFIG_PATH)
# ----------------------------------------------------------------------------------------------------------------------

from .client import ParserClient


logger = logging.getLogger(__name__)


def main() -> None:
    """
    Executable in entry point (__main__.py).
    """

    max_workers = 1

    client: ParserClient
    with ParserClient.manager() as client:
        client.dump_group(WEBSITE_HOMEPAGE, max_workers=max_workers)
