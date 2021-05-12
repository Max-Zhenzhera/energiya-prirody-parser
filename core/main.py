"""
Contains main function.

.. func:: main() -> None
"""

# setup logging for entire project--------------------------------------------------------------------------------------
import logging

from .settings import LOGGING_CONFIG_PATH
from .utils.logging_ import setup_logging


setup_logging(LOGGING_CONFIG_PATH)
# ----------------------------------------------------------------------------------------------------------------------

from .client import ParserClient


logger = logging.getLogger(__name__)


def main() -> None:
    """
    Executable in entry point (__main__.py).
    """

    client: ParserClient
    with ParserClient.manager() as client:
        client.dump_products(
            'https://energiya-prirody.prom.ua/g19072746-avtonomnye-solnechnye-elektrostantsii',
            max_workers=3
        )
