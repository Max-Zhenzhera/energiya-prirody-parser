"""
Entry point.
"""

import argparse
# add package to global path -------------------------------------------------------------------------------------------
import sys
import pathlib


sys.path.append(pathlib.Path(__file__).parent.parent.__str__())
# ----------------------------------------------------------------------------------------------------------------------
from core.main import main


if __name__ == '__main__':
    arguments_parser = argparse.ArgumentParser(description='Scrapping of the https://energiya-prirody.prom.ua/')

    arguments_parser.add_argument(
        '--link',
        required=False,
        help='URL on products group; by default website homepage'
    )
    arguments_parser.add_argument(
        '--directory',
        required=False,
        help='Path to dump reports; by default created in the project dir'
    )
    arguments_parser.add_argument(
        '--workers',
        required=False,
        help='Workers to request the website; by default is one'
    )

    arguments = arguments_parser.parse_args()

    main(
        link=arguments.link,
        directory=arguments.directory,
        workers=arguments.workers
    )
