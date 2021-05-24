"""
Contains product parser.

.. class:: ProductParser
    Implements parser for product page
"""

import logging
from copy import deepcopy

import bs4

from .base import BaseParser
from ..utils.normalization import normalize_unicode_string


__all__ = ['ProductParser']


logger = logging.getLogger(__name__)


class ProductParser(BaseParser):
    """
    Implements parser for product page.
    """

    def __init__(self, original_url: str, html_text: str):
        """
        Init product parser.
        All init arguments are inherited from base class.
        """

        super().__init__(original_url, html_text)

        self._soup = bs4.BeautifulSoup(html_text, 'html.parser')
        self._replace_internal_links_with_links_text()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title={self.title}, original_url={self.original_url})'

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

        if table is None:
            return {}

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
    def soup(self) -> bs4.BeautifulSoup:
        """ Get ``BeautifulSoup`` object of the parser """
        soup = self._soup

        return soup

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
        extra_images_links = [link.get('href') for link in links_html if link.get('href')]

        return extra_images_links

    @property
    def user_content_images_links(self) -> list[str]:
        """ Get links on the images in user content section """
        images_html = self._user_content_section.find_all('img')
        user_content_images_links = [image.get('src') for image in images_html if image.get('src')]

        return user_content_images_links

    @property
    def all_images_links(self) -> list[str]:
        """ Get all links on product images """
        all_images_links = list(set([self.image_link] + self.extra_images_links + self.user_content_images_links))

        return all_images_links

    @property
    def _user_content_section(self) -> bs4.Tag:
        """ Get ``bs4`` tag of the user content section """
        user_content_section = self._soup.find('div', {'class': 'b-user-content'})

        return user_content_section

    @property
    def user_content_html(self) -> str:
        """ Get html of the user content section """
        user_content_html = self._user_content_section.prettify() if self._user_content_section is not None else ''

        return user_content_html

    @property
    def user_content(self) -> str:
        """ Get product section with user content """
        user_content = self._user_content_section.text if self._user_content_section is not None else ''

        return user_content

    @property
    def characteristics(self) -> dict:
        """ Get well structured ``dict`` of the product characteristics """
        table = self._soup.find('table', {'class': 'b-product-info'})
        characteristics = self._parse_table(table)

        return characteristics

    @property
    def specification_links(self) -> list[str]:
        """ Get product specification links """
        specification_links_html = self._soup.find_all('a', {'class': 'b-spec-list__link'})
        specification_links = [specification_link.get('href') for specification_link in specification_links_html]

        return specification_links

    def _replace_internal_links_with_links_text(self) -> None:
        """ Replace all internal links (links on other website resources) with links text """
        user_content_links_html = self._user_content_section.find_all('a')

        user_content_link_html: bs4.Tag
        for user_content_link_html in user_content_links_html:
            if user_content_link_html.get('href').startswith('https://energiya-prirody.prom.ua/'):
                user_content_link_html.replace_with(user_content_link_html.text)

    def get_data(self) -> dict:
        """ Get ``dict`` of main product data """
        # data = {
        #     'original_url': self.original_url,
        #     'title': self.title,
        #     'price': self.price,
        #     'image': self.image_link,
        #     'extra_images': self.extra_images_links,
        #     'user_content_images_links': self.user_content_images_links,
        #     'all_images_links': self.all_images_links,
        #     'user_content_html': self.user_content_html,
        #     'user_content': self.user_content,
        #     'characteristics': self.characteristics,
        #     'specification_links': self.specification_links
        # }

        # move to manual getting of the result to catch errors in try-except block
        # if error has been occured on parsing

        attributes_names = [
            # (attribute_name_to_set, attribute_name_to_get)
            # (name of the property in dump, name of the property in class)
            ('original_url', 'original_url'),
            ('title', 'title'),
            ('price', 'price'),
            ('image', 'image_link'),
            ('extra_images', 'extra_images_links'),
            ('user_content_images', 'user_content_images_links'),
            ('all_images', 'all_images_links'),
            ('user_content_html', 'user_content_html'),
            ('user_content_text', 'user_content'),
            ('characteristics', 'characteristics'),
            ('specification_links', 'specification_links'),
        ]

        data = {}
        for attribute_name_to_set, attribute_name_to_get in attributes_names:
            try:
                attribute_value = getattr(self, attribute_name_to_get)
            except AttributeError as error:
                logger.exception('PROGRAMMER error on parsing!', exc_info=error)
                attribute_value = None
            except (LookupError, TypeError) as error:
                logger.exception('Error on parsing!', exc_info=error)
                attribute_value = None

            data[attribute_name_to_set] = attribute_value

        return data
