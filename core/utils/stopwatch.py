"""
Contains decorator that measures time of done work.

.. decorator:: track_time(func: Callable) -> Callable
    Track time of function execution and log result of tracking
"""

import functools
import logging
import time
from typing import (
    Any,
    Callable
)


__all__ = ['track_time']


logger = logging.getLogger(__name__)


def track_time(func: Callable) -> Callable:
    """ Envelope function for tracking of time execution """
    @functools.wraps(func)
    def inner(*args, **kwargs) -> Any:
        """ Return result and log info messages about time (function execution) """

        logger.info('[TIME POINT] Start time tracking...')

        time_start = time.perf_counter()
        result = func(*args, **kwargs)
        time_finish = time.perf_counter()

        time_difference = time_finish - time_start
        logger.info(f'[TIME POINT] Finish time. Spent: {time_difference}.')

        return result

    return inner
