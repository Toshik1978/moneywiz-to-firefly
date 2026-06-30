import logging

from moneywiz.analyzer import CsvAnalyzer
from moneywiz.scheme import MwAccount, MwCurrency, MwData
from storage.transactions import TransactionsDB

LOG = logging.getLogger("test")


def empty_data(**overrides):
    base = dict(currencies=[], payees=[], categories=[], tags=[], accounts=[], transfers=[], payments=[])
    base.update(overrides)
    return MwData(**base)


def test_first_import_into_empty_db_assigns_account_currency(tmp_path):
    db = TransactionsDB(LOG, str(tmp_path / "db")).init()
    analyzer = CsvAnalyzer(LOG, db)
    data = empty_data(
        currencies=[MwCurrency(name="USD")],
        accounts=[MwAccount(name="Checking", currency="USD", balance="1000")],
    )

    analyzer.analyze(data, dedup=False)
    analyzer.commit()

    accounts = db.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].currency_id is not None
