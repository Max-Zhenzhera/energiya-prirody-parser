"""
Contains base abstract parser.

.. class:: BaseParser(abc.ABC)
    Implements base abstract parser for inheriting
"""

import abc
import logging

import bs4


__all__ = ['BaseParser']


logger = logging.getLogger(__name__)


class BaseParser(abc.ABC):
    """
    Implements base abstract parser
    for inheriting.

    .. attr:: _original_url

    .. property:: original_url
    .. property:: html_text

    .. abstractproperty:: soup
    """

    def __init__(self, original_url: str, html_text: str) -> None:
        """
        Init base parser.

        :param original_url: url that refers on parsed object web page
        :type original_url: str
        :param html_text: html of the parsed object
        :type html_text: str
        """

        self._original_url = original_url
        self._html_text = html_text

    @property
    def original_url(self) -> str:
        """ Get original url of the parsed object """
        original_url = self._original_url

        return original_url

    @property
    def html_text(self) -> str:
        """ Get html text of the parsed object """
        html_text = self._html_text

        return html_text

    @property
    @abc.abstractmethod
    def soup(self) -> bs4.BeautifulSoup:
        """ Get ``BeautifulSoup`` object of the parser """
