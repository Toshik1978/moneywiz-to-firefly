from collections.abc import Mapping
from logging import Logger

from firefly_iii_client import (
    ShortAccountTypeProperty,
    TransactionSplitStore,
    TransactionStore,
    TransactionTypeProperty,
)

from firefly.client import FireflyClient
from firefly.config import Config, SettingsConfig
from helpers import to_amount
from storage.scheme import Account, Transfer
from storage.transactions import TransactionsDB


class TransferExporter:
    """Export transfers into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, Account]
    __currencies: Mapping[int, str]
    __payees: Mapping[int, str]

    __settings: SettingsConfig
    __loan_payment_category_id: str
    __loan_interest_category_id: str

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient, config: Config):
        self.__logger = logger
        self.__db = db
        self.__client = client
        self.__settings = config.settings

    def sync(self) -> None:
        """Synchronize the transfers in the database and Firefly III."""

        self.__logger.info("Sync transfers...")
        self.__accounts = {a.id: a for a in self.__db.get_accounts()}
        self.__currencies = {c.id: str(c.firefly_id) for c in self.__db.get_currencies()}
        self.__payees = {p.id: str(p.firefly_id) for p in self.__db.get_payees()}
        self.__loan_payment_category_id = next(
            str(c.firefly_id) for c in self.__db.get_categories() if c.name == self.__settings.loan_payment_category
        )
        self.__loan_interest_category_id = next(
            str(c.firefly_id) for c in self.__db.get_categories() if c.name == self.__settings.loan_interest_category
        )
        self.__sync_ff(self.__db.get_transfers())
        self.__logger.info("Sync transfers... Done")

    def __sync_ff(self, db: list[Transfer]) -> None:
        # Create transfer in Firefly
        index = 0
        skipped = 0
        try:
            for t in db:
                # Skip transfers touching an account that was never created in Firefly
                # (e.g. an account marked `ignore` in the config). Otherwise we would send
                # "None" as a source/destination id and the API would reject it.
                if not self.__has_firefly_account(t.source_id) or not self.__has_firefly_account(t.target_id):
                    skipped += 1
                    self.__logger.warning(
                        f"Skipping transfer {t.id}: references an account not exported to Firefly "
                        f"({self.__accounts[t.source_id].name} -> {self.__accounts[t.target_id].name})"
                    )
                    continue

                # Create transaction and update database object
                # It's possible to have split transfers, but we don't care and create them separately!
                ff_t = self.__to_ff(t)
                if ff_t.transactions[0].amount != "0.00":
                    t.firefly_id = self.__client.create_transaction(ff_t)
                    self.__logger.debug(f"Transfer created. Id={t.firefly_id}")

                    index += 1
                    if index % 100 == 0:
                        self.__logger.info(f"\t...{index} transfers created...")
        finally:
            self.__logger.info(f"{index} transfers created in total ({skipped} skipped)")
            self.__db.add_transfers(db)

    def __has_firefly_account(self, account_id: int) -> bool:
        account = self.__accounts.get(account_id)
        return account is not None and account.firefly_id is not None

    def __to_ff(self, t: Transfer) -> TransactionStore:
        if self.__accounts[t.target_id].firefly_type == str(ShortAccountTypeProperty.LIABILITY):
            return self.__to_ff_liability(t)

        return TransactionStore(
            transactions=[
                TransactionSplitStore(
                    type=TransactionTypeProperty.TRANSFER,
                    var_date=t.date,
                    amount=to_amount(t.source_amount),
                    currency_id=self.__currencies[t.source_currency_id],
                    source_id=str(self.__accounts[t.source_id].firefly_id),
                    destination_id=str(self.__accounts[t.target_id].firefly_id),
                    foreign_currency_id=self.__currencies[t.target_currency_id]
                    if t.source_currency_id != t.target_currency_id
                    else None,
                    foreign_amount=to_amount(t.target_amount) if t.source_currency_id != t.target_currency_id else None,
                    description=t.description if t.description else "No description",
                    external_id=str(t.id),
                )
            ]
        )

    def __to_ff_liability(self, t: Transfer) -> TransactionStore:
        # It's either withdrawal to liability account or expense (to the bank)
        dst_id = str(self.__accounts[t.target_id].firefly_id)
        category_id = self.__loan_payment_category_id
        is_interest = t.category is not None and t.category.name == self.__settings.loan_interest_category
        if is_interest and t.payee_id is not None:
            dst_id = self.__payees[t.payee_id]
            category_id = self.__loan_interest_category_id
        elif is_interest:
            # Loan interest is meant to go to a payee (the bank), but this transfer has none.
            # Keep the record by routing it to the liability account as a loan payment.
            self.__logger.warning(
                f"Loan-interest transfer {t.id} has no payee; routing to the liability account as a loan payment"
            )

        return TransactionStore(
            transactions=[
                TransactionSplitStore(
                    type=TransactionTypeProperty.WITHDRAWAL,
                    var_date=t.date,
                    amount=to_amount(t.source_amount),
                    category_id=category_id,
                    currency_id=self.__currencies[t.source_currency_id],
                    source_id=str(self.__accounts[t.source_id].firefly_id),
                    destination_id=dst_id,
                    description=t.description if t.description else "No description",
                    external_id=str(t.id),
                )
            ]
        )
