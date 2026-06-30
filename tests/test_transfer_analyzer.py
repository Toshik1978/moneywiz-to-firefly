import logging

import pytest

from moneywiz.exception import AnalyzerException
from moneywiz.scheme import MwTransfer
from moneywiz.transfer import TransferAnalyzer
from storage.scheme import Account, Currency

LOG = logging.getLogger("test")


def make_analyzer(account_names=("A", "B"), currency_names=("USD",)):
    currencies = [Currency(name=n) for n in currency_names]
    accounts = [Account(name=n, currency_id=1, balance="0") for n in account_names]
    return TransferAnalyzer(LOG, currencies, [], [], accounts)


def mw(source, target, amount, *, currency="USD", date="15/06/2024", time="10:30", category=""):
    """Build one side of a MoneyWiz transfer row."""
    return MwTransfer(
        source=source,
        target=target,
        payee="",
        currency=currency,
        date=date,
        time=time,
        category=category,
        description="",
        amount=amount,
        balance="0",
    )


class TestBasicLinking:
    def test_two_sides_collapse_into_one_transfer(self):
        # A -> B for 100; MoneyWiz exports this as two rows.
        rows = [mw("A", "B", "-100.00"), mw("B", "A", "100.00")]
        result = make_analyzer().analyze(rows).get()
        assert len(result) == 1

    def test_source_and_target_follow_the_negative_side(self):
        rows = [mw("A", "B", "-100.00"), mw("B", "A", "100.00")]
        t = make_analyzer().analyze(rows).get()[0]
        assert t.source.name == "A"
        assert t.target.name == "B"
        assert t.source_amount == "-100.00"
        assert t.target_amount == "100.00"

    def test_row_order_does_not_matter(self):
        # Positive side listed first.
        rows = [mw("B", "A", "100.00"), mw("A", "B", "-100.00")]
        t = make_analyzer().analyze(rows).get()[0]
        assert t.source.name == "A"
        assert t.target.name == "B"


class TestCrossCurrency:
    def test_keeps_both_currencies_and_amounts(self):
        rows = [
            mw("A", "B", "-100.00", currency="USD"),
            mw("B", "A", "90.00", currency="EUR"),
        ]
        t = make_analyzer(currency_names=("USD", "EUR")).analyze(rows).get()[0]
        assert t.source_currency.name == "USD"
        assert t.target_currency.name == "EUR"
        assert t.source_amount == "-100.00"
        assert t.target_amount == "90.00"


class TestFallbackLinking:
    def test_links_when_times_differ_same_day(self):
        rows = [mw("A", "B", "-100.00", time="10:30"), mw("B", "A", "100.00", time="11:00")]
        assert len(make_analyzer().analyze(rows).get()) == 1

    def test_links_when_days_differ_same_month(self):
        rows = [
            mw("A", "B", "-100.00", date="15/06/2024", time="10:30"),
            mw("B", "A", "100.00", date="18/06/2024", time="09:00"),
        ]
        assert len(make_analyzer().analyze(rows).get()) == 1


class TestErrorCases:
    def test_orphaned_single_side_raises(self):
        rows = [mw("A", "B", "-100.00")]
        with pytest.raises(AnalyzerException, match="rphaned"):
            make_analyzer().analyze(rows)

    def test_same_currency_amount_mismatch_raises(self):
        # Both sides link (same account pair/date/time) but amounts are not mirror images.
        rows = [mw("A", "B", "-100.00"), mw("B", "A", "90.00")]
        with pytest.raises(AnalyzerException):
            make_analyzer().analyze(rows)
