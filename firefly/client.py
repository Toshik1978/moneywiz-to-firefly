import uuid
from logging import Logger

from firefly_iii_client import (
    AccountRead,
    AccountsApi,
    AccountStore,
    AccountUpdate,
    ApiClient,
    CategoriesApi,
    CategoryRead,
    CategoryStore,
    CurrenciesApi,
    CurrencyRead,
    CurrencyStore,
    TagModelStore,
    TagRead,
    TagsApi,
    TransactionsApi,
    TransactionStore,
    configuration,
)


class FireflyClient:
    """Firefly III Client wrapper."""

    __logger: Logger
    __client: ApiClient

    def __init__(self, logger: Logger, url: str, token: str) -> None:
        self.__logger = logger
        self.__client = ApiClient(
            configuration.Configuration(host=url, access_token=token),
            header_name="Content-Type",
            header_value="application/json",
        )

    def get_currencies(self) -> list[CurrencyRead]:
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

    def get_accounts(self) -> list[AccountRead]:
        """Get accounts on the server."""

        api = AccountsApi(self.__client)
        page = 1
        accounts = []

        while True:
            r = api.list_account(x_trace_id=str(uuid.uuid4()), limit=2000, page=page)
            accounts.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return accounts

    def create_account(self, account: AccountStore) -> int:
        """Create a new account."""

        r = AccountsApi(self.__client).store_account(account, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def update_account(self, account_id: str, account: AccountUpdate) -> None:
        """Update an account."""

        AccountsApi(self.__client).update_account(id=account_id, account_update=account, x_trace_id=str(uuid.uuid4()))

    def get_categories(self) -> list[CategoryRead]:
        """Get categories on the server."""

        api = CategoriesApi(self.__client)
        page = 1
        categories = []

        while True:
            r = api.list_category(x_trace_id=str(uuid.uuid4()), limit=2000, page=page)
            categories.extend(r.data)
            if r.meta.pagination.current_page == r.meta.pagination.total_pages:
                break
            page += 1

        return categories

    def create_category(self, category: CategoryStore) -> int:
        """Create a new category."""

        r = CategoriesApi(self.__client).store_category(category, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)

    def get_tags(self) -> list[TagRead]:
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

    def create_transaction(self, transaction: TransactionStore) -> int:
        """Create a new transaction."""

        r = TransactionsApi(self.__client).store_transaction(transaction, x_trace_id=str(uuid.uuid4()))
        return int(r.data.id)
