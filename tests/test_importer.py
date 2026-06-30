import logging

import pytest

from moneywiz.exception import ImporterException
from moneywiz.importer import CsvImporter

LOG = logging.getLogger("test")

HEADER = "Account,Name,Current balance,Transfers,Payee,Category,Description,Amount,Balance,Currency,Date,Time,Tags"


def write_csv(tmp_path, *rows):
    path = tmp_path / "report.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return str(path)


class TestRowClassification:
    def test_classifies_account_payment_and_transfer_rows(self, tmp_path):
        path = write_csv(
            tmp_path,
            "USD,Checking,1000,,,,,,,,,,",  # account (has Name)
            ",,,,Grocery,Food,Shop,-50.00,950,USD,15/06/2024,10:30,",  # payment
            "Checking,,,Savings,,,,-100.00,,USD,15/06/2024,12:00,",  # transfer (has Transfers)
        )
        data = CsvImporter(LOG).parse(path)
        assert len(data.accounts) == 1
        assert len(data.payments) == 1
        assert len(data.transfers) == 1
        assert data.accounts[0].name == "Checking"
        assert data.accounts[0].currency == "USD"

    def test_payment_currency_and_amount_preserved(self, tmp_path):
        path = write_csv(tmp_path, ",,,,Grocery,Food,Shop,-50.00,950,USD,15/06/2024,10:30,")
        data = CsvImporter(LOG).parse(path)
        assert data.payments[0].amount == "-50.00"
        assert data.payments[0].payee == "Grocery"


class TestSepHintLine:
    ROW = ",,,,Grocery,Food,Shop,-50.00,950,USD,15/06/2024,10:30,"

    def test_parses_raw_export_with_leading_sep_line(self, tmp_path):
        # Raw MoneyWiz exports prepend an Excel "sep=,"hint line before the header.
        path = tmp_path / "raw.csv"
        path.write_text("\n".join(["sep=,", HEADER, self.ROW]) + "\n", encoding="utf-8")
        data = CsvImporter(LOG).parse(str(path))
        assert len(data.payments) == 1
        assert data.payments[0].payee == "Grocery"

    def test_still_parses_files_with_sep_line_already_stripped(self, tmp_path):
        path = write_csv(tmp_path, self.ROW)
        data = CsvImporter(LOG).parse(path)
        assert len(data.payments) == 1

    def test_error_line_numbers_account_for_skipped_sep_line(self, tmp_path, caplog):
        broken_header = (
            "Account,Name,Current balance,Transfers,Payee,Category,Description,Balance,Currency,Date,Time,Tags"
        )
        path = tmp_path / "raw_broken.csv"
        # sep line (1), header (2), bad payment row (3)
        path.write_text(
            "\n".join(["sep=,", broken_header, ",,,,Grocery,Food,Shop,950,USD,15/06/2024,10:30,"]) + "\n",
            encoding="utf-8",
        )
        with caplog.at_level("ERROR"), pytest.raises(ImporterException):
            CsvImporter(LOG).parse(str(path))
        # The physical line of the bad row reflects the skipped sep line.
        assert "row 3" in caplog.text


class TestFailLoud:
    def test_missing_column_raises_instead_of_dropping_rows(self, tmp_path):
        # Header without the Amount column; the payment row can't be parsed.
        broken_header = (
            "Account,Name,Current balance,Transfers,Payee,Category,Description,Balance,Currency,Date,Time,Tags"
        )
        path = tmp_path / "broken.csv"
        path.write_text(
            broken_header + "\n,,,,Grocery,Food,Shop,950,USD,15/06/2024,10:30,\n",
            encoding="utf-8",
        )
        with pytest.raises(ImporterException, match="Failed to parse 1 row"):
            CsvImporter(LOG).parse(str(path))

    def test_reports_count_of_all_failed_rows(self, tmp_path):
        broken_header = (
            "Account,Name,Current balance,Transfers,Payee,Category,Description,Balance,Currency,Date,Time,Tags"
        )
        path = tmp_path / "broken.csv"
        path.write_text(
            broken_header
            + "\n,,,,A,Food,Shop,950,USD,15/06/2024,10:30,"
            + "\n,,,,B,Food,Shop,950,USD,16/06/2024,10:30,\n",
            encoding="utf-8",
        )
        with pytest.raises(ImporterException, match="Failed to parse 2 row"):
            CsvImporter(LOG).parse(str(path))
