"""
Contains convenient client for product parser.

.. class:: ParserClient
    Implements client for product parser
"""

import contextlib
import json
import logging
import pathlib
import time
from concurrent.futures import thread
from typing import (
    Iterable,
    Iterator,
    Optional
)
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tqdm import (
    trange,
    tqdm
)
from tqdm.contrib.concurrent import thread_map

from .parsers import (
    ProductParser,
    ProductsAssortmentParser
)
from .settings import (
    DEFAULT_DUMP_DIR,
    DEFAULT_CLIENT_HEADERS,
    DEFAULT_MINUTES_TO_SLEEP_ON_NETWORK_ERROR_IN_FUNCTION,
    DEFAULT_MINUTES_TO_SLEEP_ON_ERROR,
    LOGGING_CONFIG_PATH
)
from .types import Product
from .utils.stopwatch import track_time


__all__ = ['ParserClient']


logger = logging.getLogger(__name__)
# set tqdm stream for logging ------------------------------------------------------------------------------------------
# for logger_handler in logger.handlers:
#     if isinstance(logger_handler, logging.StreamHandler) and logger.level == logging.INFO:
#         logger_handler.setStream(tqdm)
# ----------------------------------------------------------------------------------------------------------------------


class ParserClient:
    """
    Implements client for product parser.

    ..property:: dump_dir(self) -> pathlib.Path

    .. staticmethod:: _sleep_with_tqdm_bar(seconds: int) -> None
        Sleep with ``tqdm`` progress bar
    .. staticmethod:: _dump_product_in_json(products_dump_dir: pathlib.Path, product: Product, *,
            prefix: Optional[str] = '') -> pathlib.Path
        Dump one product in json

    .. method:: _dump_all_products_in_json(self, products_dump_dir: pathlib.Path, products: list[Product]) -> None
        Dump all products in json
    .. method:: _get_products_links(self, url: str) -> list[str]
        Get all links on products from url that refers on page with products assortment
    .. method:: _get_product(self, url: str) -> Product
        Get product instance
    .. method:: _prepare_dir_for_products(self, url: str, products_dump_dir_name: Optional[str] = None
            ) -> pathlib.Path:
        Prepare dir for products dump
    .. method:: _fetch_products_with_thread_pool_executor(self, links: Iterable[str], *,
            max_workers: Optional[int] = None) -> Iterator[Product]
        Fetch iterator of products (with ``_get_product`` results executed by thread pool)
    .. method:: dump_products(self, url: str, products_dump_dir_name: Optional[str] = None, *,
            max_workers: Optional[int] = None,
            products_dump_dir_from_broken_invocation: Optional[pathlib.Path] = None,
            left_links_for_handling_from_broken_invocation: Optional[Iterable[str]] = None,
            prepared_products_from_broken_invocation: Optional[list[Product]] = None
            ) -> None
        Dump all products by url that refers on page with products assortment
    .. method:: dump_product(self, url: str, products_dump_dir_name: Optional[str] = None) -> None
        Dump one product
    .. method:: manager(cls, *args, **kwargs) -> 'ParserClient'
        Context manager for parser client
    .. method:: close(self) -> None
        Close parser client
    """

    def __init__(self, dump_dir: Optional[str] = None, client: Optional[httpx.Client] = None):
        """
        Init environment for client [create dump dir, init http client].

        :param dump_dir: absolute path to dump dir
        :type dump_dir: Optional[str]
        """

        if dump_dir is None:
            self._dump_dir = DEFAULT_DUMP_DIR
            logger.info(
                f'Dump dir has NOT been passed. For dump reports will be used dir with path: {self._dump_dir!s}'
            )

        else:
            self._dump_dir = pathlib.Path(dump_dir)
            logger.info(
                f'Dump dir has been passed. For dump reports will be used dir with path: {self._dump_dir!s}'
            )

        if not self._dump_dir.exists():
            self._dump_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f'Dump dir has been created. Path: {self._dump_dir!s}')

        if client is None:
            self._client = httpx.Client(headers=DEFAULT_CLIENT_HEADERS)
            logger.debug('Http client has been created.')
        else:
            self._client = client
            logger.debug('Passed http client has been set.')

    def __repr__(self) -> str:
        return f'ParserClient(dump_dir={self._dump_dir}, client={self._client})'

    @property
    def dump_dir(self) -> pathlib.Path:
        """ Get dump dir """
        return self._dump_dir

    @staticmethod
    def _sleep_with_tqdm_bar(seconds: int) -> None:
        """
        Sleep for n-seconds with ``tqdm`` progress bar.

        :param seconds: seconds to sleep
        :type seconds: int

        :return: None
        :rtype: None
        """
        logger.info(f'Sleeping for {seconds} second[s]...')
        for _ in trange(seconds):
            time.sleep(1)
        logger.info(f'Have woken up after {seconds} second[s] of sleeping. Trying to work again...')

    @staticmethod
    def _dump_product_in_json(products_dump_dir: pathlib.Path, product: Product,
                              *,
                              prefix: Optional[str] = ''
                              ) -> pathlib.Path:
        """
        Dump one product in ``.json`` file.

        :param products_dump_dir: directory path for product dump
        :type products_dump_dir: pathlib.Path
        :param product: product instance
        :type product: Product
        :keyword prefix: string that will be inserted in start of the filename
        :type prefix: Optional[str]

        :return: filepath of the dumped product
        :rtype: pathlib.Path
        """

        file_extension = 'json'
        valid_product_title = product.title.replace('/', '-').replace('\\', '-').replace('\'', '').replace('\"', '')
        filename = f'{prefix}{valid_product_title}.{file_extension}'
        filepath = products_dump_dir / filename
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(product.data, file, ensure_ascii=False, indent=4)

        return filepath

    def _dump_all_products_in_json(self, products_dump_dir: pathlib.Path, products: list[Product]) -> None:
        """
        Dump all products in json.

        :param products_dump_dir: directory path for products dump
        :type products_dump_dir: pathlib.Path
        :param products: product instances
        :type products: list[Product]

        :return: dump all products in json; return none
        :rtype: None
        """

        for index, product in enumerate(products, start=1):
            prefix = f'{index:^2}-'
            product_dump_filepath = self._dump_product_in_json(products_dump_dir, product, prefix=prefix)
            log = (
                f'Product with name: {product.title}, from URL: {product.original_url}, '
                f'has been dumped in: {product_dump_filepath!s}.'
            )
            logger.info(log)

    def _get_products_links(self, url: str) -> list[str]:
        """
        Get all links on products.

        :param url: url with assortment of products
        :type url: str

        :return: list of products links
        :rtype: list[str]
        """

        try:
            response = self._client.get(url)
        except httpx.HTTPError as error:
            if isinstance(error, httpx.ReadTimeout):
                logging.exception('Error has been occured during network interacting (read timeout).')
            else:
                logging.exception('Error has been occured during network interacting.', exc_info=error)
            seconds_to_sleep = int(DEFAULT_MINUTES_TO_SLEEP_ON_NETWORK_ERROR_IN_FUNCTION * 60)
            self._sleep_with_tqdm_bar(seconds_to_sleep)
            self._get_products_links(url)
        else:
            logger.info(f'Loaded page with assortment of products with url: {url!r}')

            response_text = response.text

            parser = ProductsAssortmentParser(url, response_text)
            links = parser.links

            links_log = ''.join(f'\n\t{link}' for link in links)
            logger.info(f'Have been found {len(links)} links on the page.\nList of the links:{links_log}')

            return links

    def _get_product(self, url: str) -> Product:
        """
        Get product instance.

        :param url: url of product page
        :type url: str

        :return: product instance
        :rtype: Product
        """

        try:
            response = self._client.get(url)
        except httpx.HTTPError as error:
            if isinstance(error, httpx.ReadTimeout):
                logging.exception('Error has been occured during network interacting (read timeout).')
            else:
                logging.exception('Error has been occured during network interacting.', exc_info=error)
            seconds_to_sleep = int(DEFAULT_MINUTES_TO_SLEEP_ON_NETWORK_ERROR_IN_FUNCTION * 60)
            self._sleep_with_tqdm_bar(seconds_to_sleep)

            return self._get_product(url)
        else:
            logger.info(f'Loaded page with product. URL: {url!r}')

            response_text = response.text

            parser = ProductParser(url, response_text)
            product = Product(parser)
            logger.info(f'Parsed product with name: {product.title}. From URL: {url}')

            return product

    def _prepare_dir_for_products(self, url: str, products_dump_dir_name: Optional[str] = None) -> pathlib.Path:
        """
        Prepare directory for future products
        and return path to it.

        :param url: used for generating directory name if passed directory name is empty
        :type url: str
        :param products_dump_dir_name: directory name for dump of products data
        :type products_dump_dir_name: Optional[str]

        :return: path to the directory for products data
        :rtype: pathlib.Path
        """

        if products_dump_dir_name is None:
            products_dump_dir_name = urlparse(url).path.replace('/', '-')
            log = (
                f'Directory name for products data dump has NOT been passed. '
                f'Default one is generated: {products_dump_dir_name}'
            )
            logger.info(log)
        else:
            logger.info(f'Directory name for products data dump has been passed: {products_dump_dir_name}')

        products_dump_dir = self._dump_dir / products_dump_dir_name
        products_dump_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f'Products dump dir has been created. Path: {products_dump_dir!s}')

        return products_dump_dir

    def _fetch_products_with_thread_pool_executor(self, links: Iterable[str], *, max_workers: Optional[int] = None
                                                  ) -> Iterator[Product]:
        """
        Fetch iterator of the products.
        Returned iterator of the results of ``_get_product`` method.

        Note: iterator might contain error that has occurred during
        thread pool execution.

        :param links: links that refer on the product web pages
        :type links: Iterable[str]
        :param max_workers: max workers of the pool
        :type max_workers: Optional[int]

        :return: iterator of products
        :rtype: Iterator[Product]
        """

        thread_pool_params = {
            'max_workers': max_workers,
            'thread_name_prefix': f'{self.__class__.__name__}.dump_products'
        }

        with thread.ThreadPoolExecutor(**thread_pool_params) as executor:
            logger.info(f'Quantity of used workers in pool: {executor._max_workers}.')
            products_iterator: Iterator[Product] = executor.map(
                self._get_product,
                links
            )

        return products_iterator

        # --------------------------------------------------------------------------------------------------------------

        # # for errors raising
        # products: list[Product] = list(products_iterator)

        # --------------------------------------------------------------------------------------------------------------

        # # # # with ``tqdm.thread_map``
        # # # Note: return list - no iterator
        # # # tqdm.std.TqdmKeyError: "Unknown argument(s): {'thread_name_prefix': 'ParserClient.dump_products'}"
        # thread_pool_params.pop('thread_name_prefix')
        # products: list[Product] = thread_map(
        #     self._get_product,
        #     links,
        #     **thread_pool_params
        # )

    @track_time
    def dump_products(self, url: str, products_dump_dir_name: Optional[str] = None,
                      *,
                      max_workers: Optional[int] = None,
                      products_dump_dir_from_broken_invocation: Optional[pathlib.Path] = None,
                      left_links_for_handling_from_broken_invocation: Optional[Iterable[str]] = None,
                      prepared_products_from_broken_invocation: Optional[list[Product]] = None
                      ) -> None:
        """
        Dump data of the products in directory with ``.json`` files
        by url that refers on page with product assortment.

        Note:
            If method has been invoked
            by broken previous invocation
            it must supply all params with ``_from_broken_invocation`` ending
            so it can provide continuing of work

        :param url: url that refers on page with product assortment
        :type url: str
        :param products_dump_dir_name: directory name for dump of products data
        :type products_dump_dir_name: Optional[str]
        :keyword max_workers: num of the max workers in pool
        :type max_workers: Optional[int]
        :keyword products_dump_dir_from_broken_invocation: filepath to products dump dir
        :type products_dump_dir_from_broken_invocation: Optional[pathlib.Path]
        :keyword left_links_for_handling_from_broken_invocation: links that
            left for handling from previous method invocation that
            has been broken by network error that
            occurred on thread pool result iteration
            (so, links that are left unhandled are computed
            from broken invocation and passed here)
        :type left_links_for_handling_from_broken_invocation: Optional[Iterable[str]]
        :keyword prepared_products_from_broken_invocation: products data from
            previous method invocation that has been broken by
            network error that occurred on thread pool result iteration
            (so, part of requests that have been finished successfully
            are added in this list)
        :type prepared_products_from_broken_invocation: Optional[list[Product]]

        :return: dump products in the ``.json`` files; return none
        :rtype: None
        """

        if not prepared_products_from_broken_invocation:
            products_dump_dir = self._prepare_dir_for_products(url, products_dump_dir_name)
            logger.info(f'Products from url: {url!r} | will be saved in: {products_dump_dir!s}')
            links = self._get_products_links(url)
            products: list[Product] = []
        else:
            if not products_dump_dir_from_broken_invocation or not left_links_for_handling_from_broken_invocation:
                message = (
                    'Data from broken invocation are not complected. '
                    f'Product dump dir: {products_dump_dir_from_broken_invocation!r}. '
                    f'Left links: {left_links_for_handling_from_broken_invocation!r}'
                )
                raise ValueError(message)

            products_dump_dir = products_dump_dir_from_broken_invocation
            links = left_links_for_handling_from_broken_invocation
            products: list[Product] = prepared_products_from_broken_invocation

            links_log = '\n\t'.join(links)
            logger.info(f'Working with data from broken method invocation. Left links:\n{links_log}')

        logger.info('STARTING [DOWNLOADING | PARSING] PROCESS.')
        products_iterator = self._fetch_products_with_thread_pool_executor(links, max_workers=max_workers)

        try:
            for product in products_iterator:
                products.append(product)
        # except error that might have been raised
        # but actually waking on getting generator result (with error)
        except Exception as error:
            logging.exception('Error has been occured during network interacting.', exc_info=error)

            seconds_to_sleep = int(DEFAULT_MINUTES_TO_SLEEP_ON_ERROR * 60)
            self._sleep_with_tqdm_bar(seconds_to_sleep)

            handled_links = {product.original_url for product in products}
            unhandled_links = set(links) - handled_links

            return self.dump_products(
                url,
                max_workers=max_workers,
                products_dump_dir_from_broken_invocation=products_dump_dir,
                left_links_for_handling_from_broken_invocation=unhandled_links,
                prepared_products_from_broken_invocation=products
            )
        else:
            log = (
                'Process of [downloading | parsing] has been finished SUCCESSFULLY. '
                f'All products have been parsed. From URL: {url}.'
            )
            logger.info(log)

            logger.info('STARTING [DUMPING] PROCESS.')
            self._dump_all_products_in_json(products_dump_dir, products)
            log = (
                'Process of [dumping] has been finished SUCCESSFULLY. '
                f'All products have been dumped. From URL: {url}.'
            )
            logger.info(log)

            log = '\n\t'.join(
                (
                    'All work has been SUCCESSFULLY finished.',
                    f'Report in: {products_dump_dir!s}.',
                    f'Logs in: filepath indicated in config ({LOGGING_CONFIG_PATH}).',
                )
            )
            logger.info(log)

    @track_time
    def dump_product(self, url: str, products_dump_dir_name: Optional[str] = None) -> None:
        """
        Dump one product in the directory with ``.json`` file
        by url that refers on page with product info.

        :param url: url that refers on page with product
        :type url: str
        :param products_dump_dir_name: directory name for dump of product data
        :type products_dump_dir_name: Optional[str]

        :return: dump product data in the ``.json`` files; return none
        :rtype: None
        """

        products_dump_dir = self._prepare_dir_for_products(url, products_dump_dir_name)
        logger.info(f'Product from url: {url!r} | will be saved in: {products_dump_dir!s}')

        logger.info('STARTING [DOWNLOADING | PARSING] PROCESS.')
        try:
            product_data = self._get_product(url)
        except Exception as error:
            logging.exception('Error has been occured during network requesting.', exc_info=error)

            seconds_to_sleep = int(DEFAULT_MINUTES_TO_SLEEP_ON_ERROR * 60)
            self._sleep_with_tqdm_bar(seconds_to_sleep)

            return self.dump_product(url)
        else:
            log = (
                'Process of [downloading | parsing] has been finished SUCCESSFULLY. '
                f'Product has been parsed. From URL: {url}.'
            )
            logger.info(log)

            logger.info('STARTING [DUMPING] PROCESS.')
            # to use function that dumps all products (convenient way)
            # here create list
            product_in_list = [product_data]
            self._dump_all_products_in_json(products_dump_dir, product_in_list)
            log = (
                'Process of [dumping] has been finished SUCCESSFULLY. '
                f'Product has been dumped. From URL: {url}.'
            )
            logger.info(log)

            log = '\n\t'.join(
                (
                    'All work has been SUCCESSFULLY finished.',
                    f'Dumps in: {products_dump_dir!s}.',
                    f'Logs in: filepath indicated in config ({LOGGING_CONFIG_PATH}).',
                )
            )
            logger.info(log)

    @classmethod
    @contextlib.contextmanager
    def manager(cls, *args, **kwargs) -> 'ParserClient':
        """ Context manager for ``ParserClient`` """
        self = cls(*args, **kwargs)

        try:
            yield self
        finally:
            self.close()

    def close(self) -> None:
        """ Close parser client """
        self._client.close()
        logger.info('Parser client has been closed.')
