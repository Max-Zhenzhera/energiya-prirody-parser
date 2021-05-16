"""
Contains parsers.
"""

from .base import BaseParser
from .product import ProductParser
from .products_assortment import ProductsAssortmentParser
from .products_groups import ProductsGroupsParser


__all__ = [
    'BaseParser',
    'ProductParser',
    'ProductsAssortmentParser',
    'ProductsGroupsParser'
]
