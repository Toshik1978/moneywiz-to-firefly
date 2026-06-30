import uuid
from collections.abc import Mapping
from logging import Logger

from firefly_iii_client import TransactionSplitStore, TransactionStore, TransactionTypeProperty

from firefly.client import FireflyClient
from helpers import hash_key, to_amount
from storage.scheme import Account, Payment
from storage.transactions import TransactionsDB


class PaymentExporter:
    """Export payments into Firefly III."""

    __logger: Logger
    __db: TransactionsDB
    __client: FireflyClient
    __accounts: Mapping[int, Account]
    __categories: Mapping[int, str]
    __payees: Mapping[int, str]

    def __init__(self, logger: Logger, db: TransactionsDB, client: FireflyClient):
        self.__logger = logger
        self.__db = db
        self.__client = client

    def sync(self) -> None:
        """Synchronize the payments in the database and Firefly III."""

        self.__logger.info("Sync payments...")
        self.__accounts = {a.id: a for a in self.__db.get_accounts()}
        self.__categories = {c.id: str(c.firefly_id) for c in self.__db.get_categories()}
        self.__payees = {p.id: str(p.firefly_id) for p in self.__db.get_payees()}
        self.__sync_ff(self.__db.get_payments())
        self.__logger.info("Sync payments... Done")

    def __sync_ff(self, db: list[Payment]) -> None:
        # Create payments in Firefly
        # We want to create split transactions if it's possible
        # Group by account_id -- payee_id -- date
        index = 0
        try:
            exportable = self.__filter_exportable(db)
            mapping = self.__to_dict(exportable)
            for group in mapping.values():
                # Add splits to the transaction
                t = TransactionStore(transactions=[])
                for p in group:
                    ff_p = self.__to_ff(p)
                    if ff_p.amount != "0.00":
                        t.transactions.append(ff_p)

                if t.transactions:
                    if len(t.transactions) > 1:
                        t.group_title = group[0].payee.name
                    firefly_id = self.__client.create_transaction(t)
                    self.__logger.debug(f"Payment created. Id={firefly_id}")
                    for p in group:
                        p.firefly_id = firefly_id

                    index += len(t.transactions)
                    if index % 100 == 0:
                        self.__logger.info(f"\t...{index} payments created...")
        finally:
            self.__logger.info(f"{index} payments created in total")
            self.__db.add_payments(db)

    def __filter_exportable(self, db: list[Payment]) -> list[Payment]:
        # Drop payments on an account that was never created in Firefly (e.g. an account
        # marked `ignore` in the config). Otherwise we would send "None" as the account id.
        exportable = []
        skipped = 0
        for p in db:
            account = self.__accounts.get(p.account_id)
            if account is None or account.firefly_id is None:
                skipped += 1
                self.__logger.warning(
                    f"Skipping payment {p.id}: account not exported to Firefly "
                    f"({account.name if account else p.account_id})"
                )
                continue
            exportable.append(p)
        if skipped:
            self.__logger.info(f"Skipped {skipped} payments on non-exported accounts")
        return exportable

    def __to_dict(self, db: list[Payment]) -> Mapping[str, list[Payment]]:
        mapping = {}
        for p in db:
            payee = p.payee.name if p.payee else uuid.uuid4().hex  # Unique Payee name in case it can't be split
            withdrawal = p.amount[0] == "-"
            tt = TransactionTypeProperty.WITHDRAWAL if withdrawal else TransactionTypeProperty.DEPOSIT
            key = hash_key(str(p.account.name), payee, str(tt), p.date.strftime("%d-%m-%Y-%H-%M"))
            if mapping.get(key) is None:
                mapping[key] = []
            mapping[key].append(p)
        return mapping

    def __to_ff(self, p: Payment) -> TransactionSplitStore:
        withdrawal = p.amount[0] == "-"
        account_id = str(self.__accounts[p.account_id].firefly_id)
        payee_id = self.__payees[p.payee_id] if p.payee_id else None
        return TransactionSplitStore(
            type=TransactionTypeProperty.WITHDRAWAL if withdrawal else TransactionTypeProperty.DEPOSIT,
            var_date=p.date,
            amount=to_amount(p.amount),
            source_id=account_id if withdrawal else payee_id,
            destination_id=payee_id if withdrawal else account_id,
            category_id=self.__categories[p.category_id] if p.category_id else None,
            tags=[p.tag.name] if p.tag else None,
            description=p.description if p.description else "No description",
            external_id=str(p.id),
        )
