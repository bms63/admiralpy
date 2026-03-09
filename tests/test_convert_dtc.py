"""Tests for convert_dtc_to_dt and convert_dtc_to_dtm."""

import pytest
import pandas as pd
from datetime import date, datetime

from admiralpy import convert_dtc_to_dt, convert_dtc_to_dtm


class TestConvertDtcToDt:
    def test_full_datetime_returns_date_only(self):
        """Full ISO 8601 datetime string returns the date part only."""
        result = convert_dtc_to_dt("2019-07-18T15:25:40")
        assert result == date(2019, 7, 18)

    def test_date_only_string(self):
        """Date-only string is parsed correctly."""
        result = convert_dtc_to_dt("2019-07-18")
        assert result == date(2019, 7, 18)

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        result = convert_dtc_to_dt("")
        assert result is None

    def test_partial_date_no_imputation_returns_none(self):
        """Partial date with no imputation returns None."""
        result = convert_dtc_to_dt("2019-02")
        assert result is None

    def test_partial_date_with_imputation(self):
        """Partial date with day imputation returns a date."""
        result = convert_dtc_to_dt("2019-02", highest_imputation="D",
                                    date_imputation="first")
        assert result == date(2019, 2, 1)

    def test_series_input(self):
        """pd.Series input returns a pd.Series of Timestamps."""
        s = pd.Series(["2019-07-18", "2020-01-01", ""])
        result = convert_dtc_to_dt(s)
        assert isinstance(result, pd.Series)
        assert result.iloc[0] == pd.Timestamp("2019-07-18")
        assert result.iloc[1] == pd.Timestamp("2020-01-01")
        assert pd.isnull(result.iloc[2])

    def test_series_preserves_index(self):
        """Output Series has same index as input."""
        s = pd.Series(["2019-07-18", "2020-01-01"], index=[10, 20])
        result = convert_dtc_to_dt(s)
        assert list(result.index) == [10, 20]


class TestConvertDtcToDtm:
    def test_full_datetime_string(self):
        """Full ISO 8601 datetime string is parsed."""
        result = convert_dtc_to_dtm("2019-07-18T15:25:40")
        assert result == datetime(2019, 7, 18, 15, 25, 40)

    def test_date_only_imputes_midnight(self):
        """Date-only string with time_imputation='first' gives midnight."""
        result = convert_dtc_to_dtm(
            "2019-07-18",
            highest_imputation="D",
            time_imputation="first",
        )
        assert result == datetime(2019, 7, 18, 0, 0, 0)

    def test_date_only_imputes_end_of_day(self):
        """Date-only string with time_imputation='last' gives end of day."""
        result = convert_dtc_to_dtm(
            "2019-07-18",
            highest_imputation="D",
            time_imputation="last",
        )
        assert result == datetime(2019, 7, 18, 23, 59, 59)

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        result = convert_dtc_to_dtm("")
        assert result is None

    def test_series_input(self):
        """pd.Series input returns a pd.Series of Timestamps."""
        s = pd.Series(["2019-07-18T15:25:40", ""])
        result = convert_dtc_to_dtm(s)
        assert isinstance(result, pd.Series)
        assert result.iloc[0] == pd.Timestamp("2019-07-18 15:25:40")
        assert pd.isnull(result.iloc[1])
