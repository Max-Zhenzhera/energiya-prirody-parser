"""
Contains data for working with unicode string normalization.

.. decorator:: normalize_unicode_string(func: Callable) -> Callable
    Return the normal form for the Unicode string
"""

import functools
import logging
import unicodedata
from enum import Enum
from typing import Callable


__all__ = ['NormalizationForms', 'DEFAULT_NORMALIZATION_FORM', 'normalize_unicode_string']


logger = logging.getLogger(__name__)


class NormalizationForms(Enum):
    NFC = 'NFC'
    NFKC = 'NFKC'
    NFD = 'NFD'
    NFKD = 'NFKD'


DEFAULT_NORMALIZATION_FORM = NormalizationForms.NFKD


def normalize_unicode_string(func: Callable = None,
                             *,
                             normalization_form: NormalizationForms = DEFAULT_NORMALIZATION_FORM
                             ) -> Callable:
    """ Return the normal form for the Unicode string """

    if func is None:
        return lambda func: normalize_unicode_string(
            func,
            normalization_form=normalization_form
        )

    @functools.wraps(func)
    def inner(*args, **kwargs) -> str:
        """
        Normalize result of the function.

        :return: normalized function result
        :rtype: str
        """

        normalization_form_value = normalization_form.value

        result = str(func(*args, **kwargs))
        normalized = unicodedata.normalize(normalization_form_value, result)

        logging.debug(
            f'Normalized function result with form: {normalization_form_value}.\nFrom: {result!r}\nTo: {normalized!r}'
        )

        return normalized

    return inner
