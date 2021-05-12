"""
Contains parser for products.

.. class:: ProductParser
    Implements parser for product page
"""

import logging
from copy import deepcopy

import bs4
from bs4 import BeautifulSoup

from .utils.normalization import normalize_unicode_string


__all__ = ['ProductParser']


logger = logging.getLogger(__name__)


class ProductParser:
    """
    Implements parser for product page.

    .. property:: original_url(self) -> str
    .. property:: title(self) -> str
    .. property:: price(self) -> str
    .. property:: image_link(self) -> str
    .. property:: extra_images_links(self) -> list[str]
    .. property:: user_content_images_links(self) -> list[str]
    .. property:: all_images_links(self) -> list[str]
    .. property:: _user_content_section(self) -> bs4.Tag
    .. property:: user_content(self) -> str
    .. property:: characteristics(self) -> dict

    .. staticmethod:: _parse_table(table: bs4.Tag) -> dict
        Return ``dict`` with data of the table

    .. method:: get_data(self) -> dict
        Return ``dict`` with the main product data
    """

    def __init__(self, original_url: str, html_text: str):
        """
        Build soup[parsing engine] on product page html.

        :param original_url: url of the product page
        :type original_url: str
        :param html_text: html of the product page
        :type html_text: str
        """

        self._original_url = original_url
        self._soup = BeautifulSoup(html_text, 'html.parser')

    def __repr__(self) -> str:
        return f'ProductParser(original_url={self.original_url}, title={self.title})'

    @staticmethod
    def _parse_table(table: bs4.Tag) -> dict:
        """
        Parse html table with considering:
            * <th> tags set new category group;
            * <td> create pairs of key:value for category.

        :param table: html of the table with characteristics
        :type table: bs4.Tag

        :return: structured table info
        :rtype: dict
        """

        rows = table.find_all('tr')

        table_info = {}
        category = None
        category_info = {}
        for row in rows:
            contents = row.contents

            # if len of row content is equal 1 (``th`` in ``tr``)
            if len(contents) == 1:
                tag = contents[0]

                if tag.name == 'th':

                    # if it is not the first category
                    if category is not None:
                        table_info[category] = deepcopy(category_info)
                        category_info.clear()

                    # set category for next data
                    category = tag.text.strip()

            # if len of row content is equal 2 (pair of ``td``-s in ``tr``)
            elif len(contents) == 2:
                tag_1, tag_2 = contents

                if tag_1.name == 'td' and tag_2.name == 'td':
                    title, value = tag_1.text.strip(), tag_2.text.strip()
                    category_info[title] = value

            else:
                logger.debug(f'During table parsing unknown row structure has occured: {row!r}')

        # set for the last category (``th`` tag won`t occur again)
        table_info[category] = category_info

        return table_info

    @property
    def original_url(self) -> str:
        return self._original_url

    @property
    def title(self) -> str:
        """ Get product title """
        title = self._soup.h1.text

        return title

    @property
    @normalize_unicode_string
    def price(self) -> str:
        """ Get product price """
        price_tag = self._soup.find('p', {'class': 'b-product-cost__price'})

        if price_tag is not None:
            price = price_tag.text.strip()
        else:
            price = None

        return price

    @property
    def image_link(self) -> str:
        """ Get link on the main product image """
        image_link = self._soup.find('img', {'class': 'b-product-view__image'}).get('src')

        return image_link

    @property
    def extra_images_links(self) -> list[str]:
        """ Get links on the extra product images """
        links_container = self._soup.find('div', {'class': 'b-extra-photos'})
        links_html = links_container.find_all('a', {'class': 'b-extra-photos__item'})
        extra_images_links = [link.get('href') for link in links_html]

        return extra_images_links

    @property
    def user_content_images_links(self) -> list[str]:
        """ Get links on the images in user content section """
        images_html = self._user_content_section.find_all('img')
        user_content_images_links = [image.get('src') for image in images_html]

        return user_content_images_links

    @property
    def all_images_links(self) -> list[str]:
        """ Get all links on product images """
        all_images_links = list(set([self.image_link] + self.extra_images_links + self.user_content_images_links))

        return all_images_links

    @property
    def _user_content_section(self) -> bs4.Tag:
        user_content_section = self._soup.find('div', {'class': 'b-user-content'})

        return user_content_section

    @property
    def user_content(self) -> str:
        """ Get product section with user content """
        # user_content = self._user_content_section.text

        # temporarily
        user_content_html = self._user_content_section.find_all('p', limit=1)
        user_content = '\n'.join(p.text for p in user_content_html)

        return user_content

    @property
    def characteristics(self) -> dict:
        """ Get well structured ``dict`` of the product characteristics """
        table = self._soup.find('table', {'class': 'b-product-info'})
        characteristics = self._parse_table(table)

        return characteristics

    def get_data(self) -> dict:
        """ Get ``dict`` of main product data """
        data = {
            'original_url': self.original_url,
            'title': self.title,
            'price': self.price,
            'image': self.image_link,
            'extra_images': self.extra_images_links,
            'user_content_images_links': self.user_content_images_links,
            'all_images_links': self.all_images_links,
            'user_content': self.user_content,
            'characteristics': self.characteristics,
        }

        return data
