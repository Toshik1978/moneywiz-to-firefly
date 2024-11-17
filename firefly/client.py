import uuid
from logging import Logger
from typing import List

from firefly_iii_client import ApiClient, configuration, CurrenciesApi, CurrencyStore, AccountsApi, AccountStore, \
    CurrencyRead, AccountRead, CategoryRead, CategoriesApi, Category, TagRead, TagsApi, TagModelStore, TransactionRead, \
    TransactionsApi, TransactionStore


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

    def get_currencies(self) -> List[CurrencyRead]:
        """Get currencies on the server."""

        api = CurrenciesApi(self.__client)
        page = 1
        currencies = []

        while True:
            r = api.list_currency(x_trace_id=str(uuid.uuid4()), limit=1000, page=page)
            currencies.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return currencies

    def create_currency(self, currency: CurrencyStore) -> int:
        """Create a new currency."""

        r = CurrenciesApi(self.__client).store_currency(currency, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def enable_currency(self, code: str) -> None:
        """Enable given currency."""

        CurrenciesApi(self.__client).enable_currency(code)

    def get_accounts(self) -> List[AccountRead]:
        """Get accounts on the server."""

        api = AccountsApi(self.__client)
        page = 1
        accounts = []

        while True:
            r = api.list_account(x_trace_id=str(uuid.uuid4()), limit=1000, page=page)
            accounts.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return accounts

    def create_account(self, account: AccountStore) -> int:
        """Create a new account."""

        r = AccountsApi(self.__client).store_account(account, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def get_categories(self) -> List[CategoryRead]:
        """Get categories on the server."""

        api = CategoriesApi(self.__client)
        page = 1
        categories = []

        while True:
            r = api.list_category(x_trace_id=str(uuid.uuid4()), limit=1000, page=page)
            categories.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return categories

    def create_category(self, category: Category) -> int:
        """Create a new category."""

        r = CategoriesApi(self.__client).store_category(category, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def get_tags(self) -> List[TagRead]:
        """Get tags on the server."""

        api = TagsApi(self.__client)
        page = 1
        tags = []

        while True:
            r = api.list_tag(x_trace_id=str(uuid.uuid4()), limit=1000, page=page)
            tags.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return tags

    def create_tag(self, tag: TagModelStore) -> int:
        """Create a new tag."""

        r = TagsApi(self.__client).store_tag(tag, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def get_transactions(self) -> List[TransactionRead]:
        """Get transactions on the server."""

        api = TransactionsApi(self.__client)
        page = 1
        transactions = []

        while True:
            r = api.list_transaction(x_trace_id=str(uuid.uuid4()), limit=1000, page=page)
            transactions.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return transactions

    def create_transaction(self, transaction: TransactionStore) -> int:
        """Create a new transaction."""

        r = TransactionsApi(self.__client).store_transaction(transaction, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)
