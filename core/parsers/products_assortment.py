"""
Contains products assortment parser.

.. class:: ProductsAssortmentParser
    Implements parser for the page with products assortment
"""

import logging
from urllib.parse import urljoin

import bs4

from .base import BaseParser
from ..settings import WEBSITE_HOMEPAGE


__all__ = ['ProductsAssortmentParser']


logger = logging.getLogger(__name__)


class ProductsAssortmentParser(BaseParser):
    """
    Implements parser for the page with products assortment.

    .. attr:: _soup

    .. property:: soup(self) -> bs4.BeautifulSoup
    .. property:: category(self) -> str
    .. property:: links(self) -> list[str]
    """

    def __init__(self, original_url: str, html_text: str) -> None:
        """
        Init products assortment parser.
        All init arguments are inherited from base class.
        """

        super().__init__(original_url, html_text)

        self._soup = bs4.BeautifulSoup(html_text, 'html.parser')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(category={self.category}, original_url={self.original_url})'

    @property
    def soup(self) -> bs4.BeautifulSoup:
        """ Get ``BeautifulSoup`` object of the parser """
        soup = self._soup

        return soup

    @property
    def category(self) -> str:
        """ Get category of the products assortment """
        category = self._soup.h1.text

        return category

    @property
    def links(self) -> list[str]:
        """ Get links on products web pages """
        links_html = self._soup.find_all('a', {'class': 'b-product-gallery__title'})
        links = [urljoin(WEBSITE_HOMEPAGE, link.get('href')) for link in links_html]

        return links
