import uuid
from logging import Logger
from typing import List

from firefly_iii_client import ApiClient, configuration, CurrenciesApi, CurrencyStore

from firefly.scheme import FfCurrency


class FireflyClient:
    """Firefly III Client wrapper."""

    __logger: Logger
    __client: ApiClient

    def __init__(self, logger: Logger, url: str, token: str) -> None:
        self.__logger = logger
        self.__client = ApiClient(
            configuration.Configuration(
                host=url,
                access_token=token
            ),
            header_name='Content-Type',
            header_value='application/json'
        )

    def get_currencies(self) -> List[FfCurrency]:
        """Get currencies on the server."""

        api = CurrenciesApi(self.__client)
        page = 1
        currencies = []

        while True:
            r = api.list_currency(x_trace_id=str(uuid.uuid4()), limit=100, page=page)

            for currency in r.data:
                currencies.append(
                    FfCurrency(
                        id=int(currency.id),
                        name=currency.attributes.name,
                        code=currency.attributes.code,
                        symbol=currency.attributes.symbol,
                        enabled=currency.attributes.enabled,
                    )
                )

            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return currencies

    def create_currency(self, currency: FfCurrency) -> int:
        """Create a new currency."""

        r = CurrenciesApi(self.__client).store_currency(
            CurrencyStore(
                code=currency.code,
                name=currency.name,
                symbol=currency.symbol,
            ),
            x_trace_id=str(uuid.uuid4())
        )
        return int(r.data.id)

    def enable_currency(self, code: str) -> None:
        """Enable given currency."""

        CurrenciesApi(self.__client).enable_currency(code)
