"""
Contains product data type.

.. class:: Product
    Implements product data type
"""

from ..parsers import ProductParser


__all__ = ['Product']


class Product:
    """
    Implements product data type
    that contains all needed data of product.

    .. property:: original_url(self) -> str
    .. property:: name(self) -> str
    .. property:: data(self) -> dict
    """

    def __init__(self, parser: ProductParser) -> None:
        """
        Init product data object based on product parser.

        :param parser: product parser that contains all needed data
        :type parser: ProductParser
        """

        self._parser = parser

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f'{class_name}(title={self.title}, original_url={self.original_url})'

    @property
    def original_url(self) -> str:
        """ Get product original url. Based on ``ProductParser.original_url`` """
        original_url = self._parser.original_url

        return original_url

    @property
    def title(self) -> str:
        """ Get product title. Based on ``ProductParser.title`` """
        product_name = self._parser.title

        return product_name

    @property
    def data(self) -> dict:
        """ Get product data that prepared for dumping. Based on ``ProductParser.get_data()`` """
        data = self._parser.get_data()

        return data
