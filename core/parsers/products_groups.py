"""
Contains products groups parser.

.. class:: ProductsGroupsParser
    Implements parser for the page with products groups
"""

import logging
from urllib.parse import urljoin

import bs4

from .base import BaseParser
from ..settings import WEBSITE_HOMEPAGE


__all__ = ['ProductsGroupsParser']


logger = logging.getLogger(__name__)


class ProductsGroupsParser(BaseParser):
    """
    Implements parser for the page with products groups.
    """

    def __init__(self, original_url: str, html_text: str) -> None:
        """
        Init products groups parser.
        All init arguments are inherited from base class.
        """

        super().__init__(original_url, html_text)

        self._soup = bs4.BeautifulSoup(html_text, 'html.parser')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(group={self.group}, original_url={self.original_url})'

    @property
    def soup(self) -> bs4.BeautifulSoup:
        """ Get ``BeautifulSoup`` object of the parser """
        soup = self._soup

        return soup

    @property
    def group(self) -> str:
        """ Get group title of the products assortment """
        group = self._soup.h1.text

        return group

    @property
    def subgroups_links(self) -> list[str]:
        """ Get links on the group subgroups """
        links_html = self._soup.find_all('a', {'class': 'b-product-groups-gallery__title'})
        links = [urljoin(WEBSITE_HOMEPAGE, link.get('href')) for link in links_html]

        return links
