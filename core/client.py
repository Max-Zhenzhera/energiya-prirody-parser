"""
Contains convenient client for product parser.

.. class:: ParserClient
    Implements client for product parser
"""

import json
import logging
import pathlib
import time
from concurrent.futures import thread
from typing import (
    Iterator,
    Optional
)
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from .parsers import ProductParser
from .settings import (
    DEFAULT_DUMP_DIR,
    DEFAULT_CLIENT_HEADERS,
    DEFAULT_MINUTES_TO_SLEEP_ON_NETWORK_ERROR,
    LOGGING_CONFIG_PATH
)
from .utils.stopwatch import track_time


__all__ = ['ParserClient']


logger = logging.getLogger(__name__)
# set tqdm stream for logging ------------------------------------------------------------------------------------------
for logger_handler in logger.handlers:
    if isinstance(logger_handler, logging.StreamHandler) and logger.level == logging.INFO:
        logger_handler.setStream(tqdm)
# ----------------------------------------------------------------------------------------------------------------------


class ParserClient:
    """
    Implements client for product parser.

    .. staticmethod:: _dump_product_in_json(products_dump_dir: pathlib.Path, product_name: str, product_data: dict
            ) -> pathlib.Path
        Dump one product in json

    .. method:: _dump_all_products_in_json(self, products_dump_dir: pathlib.Path,
            products_data: Iterator[tuple[str, str, dict]]) -> None
        Dump all products in json
    .. method:: _get_all_products_links(self, url: str) -> list[str]
        Get all links on products from url that refers on page with products assortment
    .. method:: _get_product_data(self, url: str) -> tuple[str, str, dict]
        Get tuple of: product url, product name, product data
    .. method:: _prepare_dir_for_products_data(self, url: str, products_dump_dir_name: Optional[str] = None
            ) -> pathlib.Path
        Prepare dir for products dump
    .. method:: dump_products(self, url: str, products_dump_dir_name: Optional[str] = None) -> None
        Dump all products by url that refers on page with products assortment
    .. method:: dump_product(self, url: str, products_dump_dir_name: Optional[str] = None) -> None
        Dump one product
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
        return f'ParserClient(_dump_dir={self._dump_dir}, client={self._client})'

    @property
    def dump_dir(self) -> pathlib.Path:
        """ Get dump dir """
        return self._dump_dir

    @staticmethod
    def _dump_product_in_json(products_dump_dir: pathlib.Path, product_name: str, product_data: dict) -> pathlib.Path:
        """
        Dump one product in ``.json`` file.

        :param products_dump_dir: directory path for product dump
        :type products_dump_dir: pathlib.Path
        :param product_name: name of the product
        :type product_name: str
        :param product_data: data of the product
        :type product_data: dict

        :return: filepath of the dumped product
        :rtype: pathlib.Path
        """

        file_extension = '.json'
        valid_product_name = product_name.replace('/', '-').replace('\\', '-').replace('\'', '').replace('\"', '')
        filename = valid_product_name + file_extension
        filepath = products_dump_dir / filename
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(product_data, file, ensure_ascii=False, indent=4)

        return filepath

    def _dump_all_products_in_json(self,
                                   products_dump_dir: pathlib.Path,
                                   products_data: list[tuple[str, str, dict]]
                                   ) -> None:
        """
        Dump all products in json.

        :param products_dump_dir: directory path for products dump
        :type products_dump_dir: pathlib.Path
        :param products_data: data of the parsed products
        :type products_data: Iterator[tuple[str, str, dict]]

        :return: dump all products in json; return none
        :rtype: None
        """

        for product_url, product_name, product_data in tqdm(products_data):
            product_dump_filepath = self._dump_product_in_json(products_dump_dir, product_name, product_data)
            log = (
                f'Product with name: {product_name}, from URL: {product_url}, '
                f'has been dumped in: {product_dump_filepath!s}.'
            )
            logger.info(log)

    def _get_all_products_links(self, url: str) -> list[str]:
        """
        Get all links on products.

        :param url: url with assortment of products
        :type url: str

        :return: list of products links
        :rtype: list[str]
        """

        response = self._client.get(url)
        logger.info(f'Loaded page with assortment of products with url: {url!r}')

        parser = BeautifulSoup(response.text, 'html.parser')

        links_html = parser.find_all('a', {'class': 'b-product-gallery__title'})
        links = [link.get('href') for link in links_html]

        links_log = '\n\t'.join(links)
        logger.info(f'Have been found {len(links)} links on the page.\nList of the links:{links_log}')

        return links

    def _get_product_data(self, url: str) -> tuple[str, str, dict]:
        """
        Get tuple of values: (product name, product data).

        Structure:
            * product url  - ``str``  - url on web page with product;
            * product name - ``str``  - just product name;
            * product name - ``dict`` - ``dict`` of product data (prepared for dumping).

        :param url: url on product page
        :type url: str

        :return: product name and product data in tuple
        :rtype: tuple[str, dict]
        """

        response = self._client.get(url)
        logger.info(f'Loaded page with product. URL: {url!r}')

        response_text = response.text

        parser = ProductParser(url, response_text)
        product_name = parser.title
        product_data = parser.get_data()
        logger.info(f'Parsed product data with name: {product_name}. From URL: {url}')

        product = (url, product_name, product_data)

        return product

    def _prepare_dir_for_products_data(self, url: str, products_dump_dir_name: Optional[str] = None) -> pathlib.Path:
        """
        Prepare directory for future products data
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

    @track_time
    def dump_products(self, url: str, products_dump_dir_name: Optional[str] = None,
                      *,
                      max_workers: Optional[int] = None,
                      ) -> None:
        """
        Dump data of the products in directory with ``.json`` files
        by url that refers on page with product assortment.

        :param url: url that refers on page with product assortment
        :type url: str
        :param products_dump_dir_name: directory name for dump of products data
        :type products_dump_dir_name: Optional[str]
        :keyword max_workers: num of the max workers in pool
        :type max_workers: Optional[int]

        :return: dump products data in the ``.json`` files; return none
        :rtype: None
        """

        products_dump_dir = self._prepare_dir_for_products_data(url, products_dump_dir_name)
        logger.info(f'Products data from url: {url!r} | will be saved in: {products_dump_dir!s}')

        links = self._get_all_products_links(url)

        logger.info('STARTING [DOWNLOADING | PARSING] PROCESS.')

        thread_pool_params = {
            'max_workers': max_workers,
            'thread_name_prefix': 'ParserClient.dump_products'
        }

        # # # with ``tqdm.thread_map``
        # # tqdm.std.TqdmKeyError: "Unknown argument(s): {'thread_name_prefix': 'ParserClient.dump_products'}"
        thread_pool_params.pop('thread_name_prefix')
        products_data_iterator: Iterator[tuple[str, str, dict]] = thread_map(
            self._get_product_data,
            links,
            **thread_pool_params
        )

        # # # # without ``tqdm``
        # with thread.ThreadPoolExecutor(**thread_pool_params) as executor:
        #     logger.info(f'Quantity of used workers in pool: {executor._max_workers}.')
        #     products_data_iterator: Iterator[tuple[str, str, dict]] = executor.map(
        #         self._get_product_data,
        #         links
        #     )

        # # for errors raising
        # products_data: list[tuple[str, str, dict]] = list(products_data)

        products_data = []
        try:
            for product_data in products_data_iterator:
                products_data.append(product_data)
        # except error that might have been raised
        # but actually waking on getting generator result (with error)
        except httpx.ReadTimeout as error:
            logging.exception('Error has been occured during network requesting.', exc_info=error)

            minutes_to_sleep = DEFAULT_MINUTES_TO_SLEEP_ON_NETWORK_ERROR
            logger.info(f'Sleeping for {minutes_to_sleep} minute[s]...')
            time.sleep(60 * minutes_to_sleep)

            logger.info(f'Have woken up after {minutes_to_sleep} minute[s] of sleeping. Trying to work again...')
            self.dump_products(url, )
        else:
            log = (
                'Process of [downloading | parsing] has been finished SUCCESSFULLY. '
                f'All products have been parsed. From URL: {url}.'
            )
            logger.info(log)

            logger.info('STARTING [DUMPING] PROCESS.')
            self._dump_all_products_in_json(products_dump_dir, products_data)
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
        Dump data of one product in directory with ``.json`` file
        by url that refers on page with product info.

        :param url: url that refers on page with product
        :type url: str
        :param products_dump_dir_name: directory name for dump of product data
        :type products_dump_dir_name: Optional[str]

        :return: dump product data in the ``.json`` files; return none
        :rtype: None
        """

        products_dump_dir = self._prepare_dir_for_products_data(url, products_dump_dir_name)
        logger.info(f'Product data from url: {url!r} | will be saved in: {products_dump_dir!s}')

        logger.info('STARTING [DOWNLOADING | PARSING] PROCESS.')
        try:
            product_data = self._get_product_data(url)
        except httpx.ReadError as error:
            logging.exception('Error has been occured during network requesting.', exc_info=error)

            minutes_to_sleep = 1
            logger.info(f'Sleeping for {minutes_to_sleep} minute[s]...')
            time.sleep(60 * minutes_to_sleep)

            logger.info(f'Have woken up after {minutes_to_sleep} minute[s] of sleeping. Trying to work again...')
            self.dump_product(url)
        else:
            log = (
                'Process of [downloading | parsing] has been finished SUCCESSFULLY. '
                f'Product has been parsed. From URL: {url}.'
            )
            logger.info(log)

            logger.info('STARTING [DUMPING] PROCESS.')
            # to use function that dumps all products (convenient way)
            # here create list
            product_data_in_list = [product_data]
            self._dump_all_products_in_json(products_dump_dir, product_data_in_list)
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

    def close(self) -> None:
        """ Close parser client """
        self._client.close()
        logger.info('Parser client has been closed.')
