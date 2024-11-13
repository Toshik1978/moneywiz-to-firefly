import uuid
from logging import Logger
from typing import List, Mapping

import requests

from firefly.scheme import FfCurrency


class FireflyClient:
    """Firefly III Client."""

    __logger: Logger
    __url: str
    __token: str

    def __init__(self, logger: Logger, url: str, token: str) -> None:
        self.__logger = logger
        self.__url = url
        self.__token = token

    def get_currencies(self) -> List[FfCurrency]:
        """Get currencies on the server."""

        page = 1
        currencies = []

        while True:
            params = {'limit': 100, 'page': page}

            r = requests.get(self.__url + '/v1/currencies', headers=self.__headers(), params=params)
            r.raise_for_status()
            j = r.json()

            for currency in j['data']:
                currencies.append(
                    FfCurrency(
                        id=int(currency['id']),
                        name=currency['attributes']['name'],
                        code=currency['attributes']['code'],
                        symbol=currency['attributes']['symbol'],
                        enabled=currency['attributes']['enabled'],
                    )
                )

            if j['meta']['pagination']['current_page'] == j['meta']['pagination']['total_pages']:
                break
            page += 1

        return currencies

    def create_currency(self, currency: FfCurrency) -> int:
        """Create a new currency."""

        payload = {"code": currency.code, "name": currency.name, "symbol": currency.symbol}
        r = requests.post(self.__url + f'/v1/currencies', headers=self.__headers(), json=payload)
        r.raise_for_status()
        j = r.json()
        return int(j['data']['id'])

    def enable_currency(self, code: str) -> None:
        """Enable given currency."""

        r = requests.post(self.__url + f'/v1/currencies/{code}/enable', headers=self.__headers())
        r.raise_for_status()

    def __headers(self) -> Mapping[str, str]:
        return {
            'Authorization': f'Bearer {self.__token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.api+json',
            'X-Trace-Id': str(uuid.uuid4()),
        }
