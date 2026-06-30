import logging
from types import SimpleNamespace

from firefly_iii_client import AccountRoleProperty, ShortAccountTypeProperty

from firefly.account import AccountExporter
from firefly.category import CategoryExporter
from firefly.config import AccountConfig, Config, SettingsConfig
from firefly.currency import CurrencyExporter
from firefly.exporter import Exporter
from firefly.payee import PayeeExporter
from firefly.tag import TagExporter
from helpers import hash_key
from storage.scheme import Account, Category, Currency, Payee, Tag
from storage.transactions import TransactionsDB

LOG = logging.getLogger("test")

ASSET = str(ShortAccountTypeProperty.ASSET)
LIABILITY = str(ShortAccountTypeProperty.LIABILITY)
EXPENSE = str(ShortAccountTypeProperty.EXPENSE)
REVENUE = str(ShortAccountTypeProperty.REVENUE)


def ff_currency(id_, code, enabled=True):
    return SimpleNamespace(id=str(id_), attributes=SimpleNamespace(code=code, enabled=enabled))


def ff_category(id_, name):
    return SimpleNamespace(id=str(id_), attributes=SimpleNamespace(name=name))


def ff_tag(id_, tag):
    return SimpleNamespace(id=str(id_), attributes=SimpleNamespace(tag=tag))


def ff_account(id_, name, type_=ASSET, active=True):
    return SimpleNamespace(id=str(id_), attributes=SimpleNamespace(name=name, type=type_, active=active))


class FakeClient:
    """Configurable fake of FireflyClient that records writes and returns canned reads."""

    def __init__(self, *, currencies=None, categories=None, tags=None, accounts=None):
        self._currencies = currencies or []
        self._categories = categories or []
        self._tags = tags or []
        self._accounts = accounts or []
        self.created_currencies = []
        self.enabled_currencies = []
        self.created_categories = []
        self.created_tags = []
        self.created_accounts = []
        self.updated_accounts = []
        self.created_transactions = []
        self._next = 5000

    def _id(self):
        self._next += 1
        return self._next

    def get_currencies(self):
        return self._currencies

    def create_currency(self, store):
        self.created_currencies.append(store)
        return self._id()

    def enable_currency(self, code):
        self.enabled_currencies.append(code)

    def get_categories(self):
        return self._categories

    def create_category(self, store):
        self.created_categories.append(store)
        return self._id()

    def get_tags(self):
        return self._tags

    def create_tag(self, store):
        self.created_tags.append(store)
        return self._id()

    def get_accounts(self):
        return self._accounts

    def create_account(self, store):
        self.created_accounts.append(store)
        return self._id()

    def update_account(self, account_id, update):
        self.updated_accounts.append((account_id, update))

    def create_transaction(self, store):
        self.created_transactions.append(store)
        return self._id()


def make_db(tmp_path):
    return TransactionsDB(LOG, str(tmp_path / "db")).init()


def make_config(accounts=None):
    return Config(
        accounts=accounts or [],
        settings=SettingsConfig(
            default_account_type="asset",
            default_account_role="defaultAsset",
            loan_payment_category="Loan Payment",
            loan_interest_category="Loan Interest",
        ),
    )


class TestCurrencyExporter:
    def test_links_creates_and_enables(self, tmp_path):
        db = make_db(tmp_path)
        db.add_currencies(
            [
                Currency(name="USD"),  # exists & enabled -> just linked
                Currency(name="EUR"),  # missing -> created
                Currency(name="GBP"),  # exists but disabled -> enabled
            ]
        )
        client = FakeClient(currencies=[ff_currency(1, "USD"), ff_currency(3, "GBP", enabled=False)])

        CurrencyExporter(LOG, db, client).sync()

        by_name = {c.name: c for c in db.get_currencies()}
        assert by_name["USD"].firefly_id == 1
        assert by_name["EUR"].firefly_id is not None  # newly created id
        assert {s.code for s in client.created_currencies} == {"EUR"}
        assert client.enabled_currencies == ["GBP"]


class TestCategoryExporter:
    def test_links_existing_and_creates_missing(self, tmp_path):
        db = make_db(tmp_path)
        db.add_categories([Category(name="Food"), Category(name="Travel")])
        client = FakeClient(categories=[ff_category(10, "Food")])

        CategoryExporter(LOG, db, client).sync()

        by_name = {c.name: c for c in db.get_categories()}
        assert by_name["Food"].firefly_id == 10
        assert by_name["Travel"].firefly_id is not None
        assert {s.name for s in client.created_categories} == {"Travel"}


class TestTagExporter:
    def test_links_existing_and_creates_missing(self, tmp_path):
        db = make_db(tmp_path)
        db.add_tags([Tag(name="vacation"), Tag(name="work")])
        client = FakeClient(tags=[ff_tag(7, "vacation")])

        TagExporter(LOG, db, client).sync()

        by_name = {t.name: t for t in db.get_tags()}
        assert by_name["vacation"].firefly_id == 7
        assert by_name["work"].firefly_id is not None
        assert {s.tag for s in client.created_tags} == {"work"}


class TestPayeeExporter:
    def test_links_existing_and_creates_with_correct_type(self, tmp_path):
        db = make_db(tmp_path)
        db.add_payees(
            [
                Payee(name="Shop", expense=True),  # exists as expense -> linked
                Payee(name="Employer", expense=False),  # missing revenue -> created
            ]
        )
        client = FakeClient(accounts=[ff_account(20, "Shop", type_=EXPENSE)])

        PayeeExporter(LOG, db, client).sync()

        by_key = {hash_key(p.name, str(p.expense)): p for p in db.get_payees()}
        shop = by_key[hash_key("Shop", "True")]
        employer = by_key[hash_key("Employer", "False")]
        assert shop.firefly_id == 20
        assert employer.firefly_id is not None
        assert {s.name for s in client.created_accounts} == {"Employer"}
        assert client.created_accounts[0].type == ShortAccountTypeProperty.REVENUE


class TestAccountExporter:
    def _usd(self, db):
        db.add_currencies([Currency(name="USD", firefly_id=1)])
        return db.get_currencies()[0]

    def test_creates_asset_account(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Savings", currency_id=usd.id, balance="0")])
        config = make_config([AccountConfig(name="Savings", type="asset", role="defaultAsset", active=True)])

        AccountExporter(LOG, db, FakeClient(), config).sync()

        acct = db.get_accounts()[0]
        assert acct.firefly_id is not None
        assert acct.firefly_type == ASSET

    def test_creates_credit_card_with_opening_balance(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Visa", currency_id=usd.id, balance="0")])
        config = make_config(
            [
                AccountConfig(
                    name="Visa",
                    type="asset",
                    role=AccountRoleProperty.CCASSET.value,
                    payment_date=31,
                    active=True,
                    opening_balance_date="01/01/2020",
                    opening_balance="100",
                )
            ]
        )
        client = FakeClient()

        AccountExporter(LOG, db, client, config).sync()

        store = client.created_accounts[0]
        assert store.account_role == AccountRoleProperty.CCASSET
        assert store.opening_balance == "100"

    def test_creates_liability_account(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Mortgage", currency_id=usd.id, balance="0")])
        config = make_config(
            [AccountConfig(name="Mortgage", type="liability", liability_type="mortgage", interest="3", active=True)]
        )
        client = FakeClient()

        AccountExporter(LOG, db, client, config).sync()

        acct = db.get_accounts()[0]
        assert acct.firefly_type == LIABILITY
        assert client.created_accounts[0].interest == "3"

    def test_ignored_account_is_not_created(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Hidden", currency_id=usd.id, balance="0")])
        config = make_config([AccountConfig(name="Hidden", ignore=True)])
        client = FakeClient()

        AccountExporter(LOG, db, client, config).sync()

        assert client.created_accounts == []
        assert db.get_accounts()[0].firefly_id is None

    def test_account_without_config_is_not_created(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Unknown", currency_id=usd.id, balance="0")])
        client = FakeClient()

        AccountExporter(LOG, db, client, make_config()).sync()

        assert client.created_accounts == []

    def test_links_existing_account_and_disables_inactive(self, tmp_path):
        db = make_db(tmp_path)
        usd = self._usd(db)
        db.add_accounts([Account(name="Old", currency_id=usd.id, balance="0")])
        # Account already exists in Firefly and is active, but config says inactive -> disable.
        config = make_config([AccountConfig(name="Old", type="asset", active=False)])
        client = FakeClient(accounts=[ff_account(300, "Old", active=True)])

        AccountExporter(LOG, db, client, config).sync()

        assert db.get_accounts()[0].firefly_id == 300
        assert client.created_accounts == []
        assert len(client.updated_accounts) == 1


class TestExporterOrchestration:
    def test_export_runs_all_phases(self, tmp_path):
        db = make_db(tmp_path)
        db.add_currencies([Currency(name="USD")])
        db.add_categories([Category(name="Food"), Category(name="Loan Payment"), Category(name="Loan Interest")])
        db.add_tags([Tag(name="vacation")])
        db.add_payees([Payee(name="Shop", expense=True)])
        client = FakeClient()

        Exporter(LOG, db, client, make_config()).export()

        # Everything got an id assigned through the full pipeline.
        assert db.get_currencies()[0].firefly_id is not None
        assert db.get_categories()[0].firefly_id is not None
        assert db.get_tags()[0].firefly_id is not None
        assert db.get_payees()[0].firefly_id is not None
