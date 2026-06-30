from datetime import datetime

import pytest

from helpers import filter_utf8, hash_key, to_amount, to_datetime


class TestToDatetime:
    def test_parses_day_month_year_and_time(self):
        assert to_datetime("15/06/2024", "10:30") == datetime(2024, 6, 15, 10, 30)

    def test_is_day_first_not_month_first(self):
        # 13 cannot be a month, proving dd/mm parsing
        assert to_datetime("13/01/2024", "00:00") == datetime(2024, 1, 13, 0, 0)

    def test_rejects_unexpected_format(self):
        with pytest.raises(ValueError):
            to_datetime("2024-06-15", "10:30")


class TestToAmount:
    def test_strips_leading_minus(self):
        assert to_amount("-50.00") == "50.00"

    def test_strips_leading_plus(self):
        assert to_amount("+50.00") == "50.00"

    def test_strips_thousands_separators(self):
        assert to_amount("-1,234.56") == "1234.56"

    def test_leaves_plain_amount_untouched(self):
        assert to_amount("99.99") == "99.99"


class TestHashKey:
    def test_joins_with_dash(self):
        assert hash_key("a", "b", "c") == "a-b-c"

    def test_single_argument(self):
        assert hash_key("only") == "only"

    def test_order_matters(self):
        assert hash_key("a", "b") != hash_key("b", "a")


class TestFilterUtf8:
    def test_replaces_non_breaking_space_with_space(self):
        assert filter_utf8("a\xa0b") == "a b"

    def test_replaces_play_glyphs_with_dash(self):
        assert filter_utf8("▶︎") == "-"
        assert filter_utf8("►") == "-"

    def test_leaves_plain_text_untouched(self):
        assert filter_utf8("Grocery Store") == "Grocery Store"
