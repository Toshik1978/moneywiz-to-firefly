import logging
from datetime import datetime

from firefly_iii_client import ShortAccountTypeProperty

from firefly.config import Config, SettingsConfig
from firefly.payment import PaymentExporter
from firefly.transfer import TransferExporter
from storage.scheme import Account, Category, Currency, Payee, Payment, Transfer
from storage.transactions import TransactionsDB

LOG = logging.getLogger("test")

LIABILITY = str(ShortAccountTypeProperty.LIABILITY)
ASSET = str(ShortAccountTypeProperty.ASSET)


class FakeClient:
    """Records created transactions and hands back incrementing ids."""

    def __init__(self):
        self.created = []
        self._next = 1000

    def create_transaction(self, transaction) -> int:
        self.created.append(transaction)
        self._next += 1
        return self._next


def make_config():
    return Config(
        accounts=[],
        settings=SettingsConfig(
            default_account_type="asset",
            default_account_role="defaultAsset",
            loan_payment_category="Loan Payment",
            loan_interest_category="Loan Interest",
        ),
    )


def seed_common(db):
    usd = Currency(name="USD", firefly_id=1)
    db.add_currencies([usd])
    food = Category(name="Food", firefly_id=10)
    loan_pay = Category(name="Loan Payment", firefly_id=11)
    loan_int = Category(name="Loan Interest", firefly_id=12)
    db.add_categories([food, loan_pay, loan_int])
    bank = Payee(name="Bank", expense=True, firefly_id=20)
    db.add_payees([bank])
    return {"usd": usd, "food": food, "loan_pay": loan_pay, "loan_int": loan_int, "bank": bank}


class TestIgnoredAccountPayments:
    def test_payment_on_unexported_account_is_skipped_not_sent_as_none(self, tmp_path):
        db = TransactionsDB(LOG, str(tmp_path / "db")).init()
        seeds = seed_common(db)
        active = Account(name="Active", currency_id=seeds["usd"].id, balance="0", firefly_id=100, firefly_type=ASSET)
        ignored = Account(name="Ignored", currency_id=seeds["usd"].id, balance="0", firefly_id=None)
        db.add_accounts([active, ignored])

        db.add_payments(
            [
                Payment(
                    account_id=active.id,
                    category_id=seeds["food"].id,
                    description="ok",
                    date=datetime(2024, 6, 15, 10, 30),
                    amount="-50.00",
                    balance="0",
                ),
                Payment(
                    account_id=ignored.id,
                    category_id=seeds["food"].id,
                    description="skip",
                    date=datetime(2024, 6, 16, 10, 30),
                    amount="-10.00",
                    balance="0",
                ),
            ]
        )

        client = FakeClient()
        PaymentExporter(LOG, db, client).sync()

        # Only the payment on the exported account is sent.
        assert len(client.created) == 1
        # The skipped payment keeps firefly_id == None (still returned by get_payments).
        remaining = {p.description for p in db.get_payments()}
        assert "skip" in remaining
        assert "ok" not in remaining
        # And no "None" string was ever sent as an account id.
        for tx in client.created:
            for s in tx.transactions:
                assert s.source_id != "None"
                assert s.destination_id != "None"


class TestLiabilityTransferWithoutPayee:
    def _liability_transfer(self, db, seeds, *, payee_id, category_id):
        src = Account(name="Checking", currency_id=seeds["usd"].id, balance="0", firefly_id=100, firefly_type=ASSET)
        loan = Account(name="Loan", currency_id=seeds["usd"].id, balance="0", firefly_id=200, firefly_type=LIABILITY)
        db.add_accounts([src, loan])
        db.add_transfers(
            [
                Transfer(
                    source_id=src.id,
                    target_id=loan.id,
                    payee_id=payee_id,
                    category_id=category_id,
                    description="loan",
                    date=datetime(2024, 6, 15, 10, 30),
                    source_amount="-10.00",
                    source_currency_id=seeds["usd"].id,
                    source_balance="0",
                    target_amount="10.00",
                    target_currency_id=seeds["usd"].id,
                    target_balance="0",
                )
            ]
        )

    def test_loan_interest_without_payee_does_not_crash(self, tmp_path):
        db = TransactionsDB(LOG, str(tmp_path / "db")).init()
        seeds = seed_common(db)
        # Loan-interest transfer but no payee to route the interest to.
        self._liability_transfer(db, seeds, payee_id=None, category_id=seeds["loan_int"].id)

        client = FakeClient()
        TransferExporter(LOG, db, client, make_config()).sync()

        # It is still exported (not dropped) and nothing is sent as a "None" destination.
        assert len(client.created) == 1
        split = client.created[0].transactions[0]
        assert split.destination_id != "None"


class TestTransferOnUnexportedAccount:
    def test_transfer_referencing_ignored_account_is_skipped(self, tmp_path):
        db = TransactionsDB(LOG, str(tmp_path / "db")).init()
        seeds = seed_common(db)
        src = Account(name="Checking", currency_id=seeds["usd"].id, balance="0", firefly_id=100, firefly_type=ASSET)
        ignored = Account(name="Ignored", currency_id=seeds["usd"].id, balance="0", firefly_id=None)
        db.add_accounts([src, ignored])
        db.add_transfers(
            [
                Transfer(
                    source_id=src.id,
                    target_id=ignored.id,
                    payee_id=None,
                    category_id=None,
                    description="to ignored",
                    date=datetime(2024, 6, 15, 10, 30),
                    source_amount="-10.00",
                    source_currency_id=seeds["usd"].id,
                    source_balance="0",
                    target_amount="10.00",
                    target_currency_id=seeds["usd"].id,
                    target_balance="0",
                )
            ]
        )

        client = FakeClient()
        TransferExporter(LOG, db, client, make_config()).sync()

        assert len(client.created) == 0
