"""
Contains parsers.
"""

from .base import BaseParser
from .product import ProductParser
from .products_assortment import ProductsAssortmentParser


__all__ = [
    'BaseParser',
    'ProductParser',
    'ProductsAssortmentParser'
]
