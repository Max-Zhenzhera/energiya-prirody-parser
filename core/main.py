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

    # do something
    client = ParserClient()

    url = 'https://energiya-prirody.prom.ua/g26846814-biolux'
    client.dump_products(url)

