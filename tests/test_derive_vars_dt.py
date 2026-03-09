"""Tests for derive_vars_dt and derive_vars_dtm."""

import pytest
import pandas as pd
import numpy as np
from pandas import Timestamp, NaT

from admiralpy import derive_vars_dt, derive_vars_dtm


# ---------------------------------------------------------------------------
# derive_vars_dt
# ---------------------------------------------------------------------------


class TestDeriveVarsDt:
    """Tests for derive_vars_dt()."""

    def test_complete_dates_no_imputation(self):
        """Complete ISO 8601 dates are converted correctly without imputation."""
        df = pd.DataFrame(
            {
                "MHSTDTC": [
                    "2019-07-18T15:25:40",
                    "2019-07-18T15:25",
                    "2019-07-18",
                ]
            }
        )
        result = derive_vars_dt(df, new_vars_prefix="AST", dtc="MHSTDTC")

        assert "ASTDT" in result.columns
        assert result.loc[0, "ASTDT"] == Timestamp("2019-07-18")
        assert result.loc[1, "ASTDT"] == Timestamp("2019-07-18")
        assert result.loc[2, "ASTDT"] == Timestamp("2019-07-18")

    def test_missing_and_empty_dtc(self):
        """Missing and empty DTC values produce NaT."""
        df = pd.DataFrame({"QSDTC": ["2019-07-18", "", None, np.nan]})
        result = derive_vars_dt(df, new_vars_prefix="A", dtc="QSDTC")

        assert result.loc[0, "ADT"] == Timestamp("2019-07-18")
        assert pd.isnull(result.loc[1, "ADT"])
        assert pd.isnull(result.loc[2, "ADT"])
        assert pd.isnull(result.loc[3, "ADT"])

    def test_impute_day_first(self):
        """Year-month DTC is imputed to first day."""
        df = pd.DataFrame({"QSDTC": ["2019-02"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="D",
            date_imputation="first",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-02-01")

    def test_impute_day_last(self):
        """Year-month DTC is imputed to last day of month."""
        df = pd.DataFrame({"QSDTC": ["2019-02"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="D",
            date_imputation="last",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-02-28")

    def test_impute_day_mid(self):
        """Year-month DTC is imputed to 15th."""
        df = pd.DataFrame({"QSDTC": ["2019-02"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="D",
            date_imputation="mid",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-02-15")

    def test_impute_month_and_day_first(self):
        """Year-only DTC is imputed to Jan 1st."""
        df = pd.DataFrame({"QSDTC": ["2019"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="M",
            date_imputation="first",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-01-01")

    def test_impute_month_and_day_last(self):
        """Year-only DTC is imputed to Dec 31st."""
        df = pd.DataFrame({"QSDTC": ["2019"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="M",
            date_imputation="last",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-12-31")

    def test_impute_month_and_day_mid(self):
        """Year-only DTC is imputed to June 30."""
        df = pd.DataFrame({"QSDTC": ["2019"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="M",
            date_imputation="mid",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-06-30")

    def test_no_imputation_for_partial_dates_when_highest_is_n(self):
        """Partial dates yield NaT when highest_imputation='n'."""
        df = pd.DataFrame({"QSDTC": ["2019-02", "2019"]})
        result = derive_vars_dt(
            df, new_vars_prefix="A", dtc="QSDTC", highest_imputation="n"
        )
        assert pd.isnull(result.loc[0, "ADT"])
        assert pd.isnull(result.loc[1, "ADT"])

    def test_flag_imputation_auto_creates_dtf_column(self):
        """Date imputation flag (DTF) is created when highest_imputation != 'n'."""
        df = pd.DataFrame({"QSDTC": ["2019-07-18", "2019-02", "2019"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="M",
            date_imputation="first",
        )
        assert "ADTF" in result.columns
        assert pd.isna(result.loc[0, "ADTF"])
        assert result.loc[1, "ADTF"] == "D"
        assert result.loc[2, "ADTF"] == "M"

    def test_flag_imputation_none_no_dtf_column(self):
        """No DTF column when flag_imputation='none'."""
        df = pd.DataFrame({"QSDTC": ["2019-02"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="M",
            flag_imputation="none",
        )
        assert "ADTF" not in result.columns

    def test_custom_prefix_creates_correct_column_names(self):
        """Custom prefix generates correctly named columns."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18"]})
        result = derive_vars_dt(df, new_vars_prefix="TRTS", dtc="EXSTDTC")
        assert "TRTSDT" in result.columns

    def test_invalid_dtc_column_raises(self):
        """ValueError raised when dtc column is missing."""
        df = pd.DataFrame({"OTHER": ["2019-07-18"]})
        with pytest.raises(ValueError, match="Column 'QSDTC' not found"):
            derive_vars_dt(df, new_vars_prefix="A", dtc="QSDTC")

    def test_invalid_highest_imputation_raises(self):
        """ValueError raised for unrecognised highest_imputation."""
        df = pd.DataFrame({"QSDTC": ["2019-07-18"]})
        with pytest.raises(ValueError, match="highest_imputation must be one of"):
            derive_vars_dt(df, new_vars_prefix="A", dtc="QSDTC", highest_imputation="X")

    def test_specific_date_imputation(self):
        """Date imputation using 'MM-DD' format."""
        df = pd.DataFrame({"QSDTC": ["2019-02"]})
        result = derive_vars_dt(
            df,
            new_vars_prefix="A",
            dtc="QSDTC",
            highest_imputation="D",
            date_imputation="04-15",
        )
        assert result.loc[0, "ADT"] == Timestamp("2019-02-15")

    def test_original_columns_preserved(self):
        """Original columns are not modified."""
        df = pd.DataFrame({"USUBJID": ["P01"], "QSDTC": ["2019-07-18"]})
        result = derive_vars_dt(df, new_vars_prefix="A", dtc="QSDTC")
        assert list(result.columns[:2]) == ["USUBJID", "QSDTC"]


# ---------------------------------------------------------------------------
# derive_vars_dtm
# ---------------------------------------------------------------------------


class TestDeriveVarsDtm:
    """Tests for derive_vars_dtm()."""

    def test_full_datetime_converted(self):
        """Full ISO 8601 datetime strings are parsed correctly."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18T15:25:40"]})
        result = derive_vars_dtm(df, new_vars_prefix="AST", dtc="EXSTDTC")
        assert result.loc[0, "ASTDTM"] == Timestamp("2019-07-18 15:25:40")

    def test_date_only_imputes_time_first(self):
        """Date-only DTC is imputed to midnight when time_imputation='first'."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18"]})
        result = derive_vars_dtm(
            df,
            new_vars_prefix="AST",
            dtc="EXSTDTC",
            highest_imputation="D",
            time_imputation="first",
        )
        assert result.loc[0, "ASTDTM"] == Timestamp("2019-07-18 00:00:00")

    def test_date_only_imputes_time_last(self):
        """Date-only DTC is imputed to end of day when time_imputation='last'."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18"]})
        result = derive_vars_dtm(
            df,
            new_vars_prefix="AST",
            dtc="EXSTDTC",
            highest_imputation="D",
            time_imputation="last",
        )
        assert result.loc[0, "ASTDTM"] == Timestamp("2019-07-18 23:59:59")

    def test_missing_dtc_gives_nat(self):
        """Empty DTC produces NaT."""
        df = pd.DataFrame({"EXSTDTC": [""]})
        result = derive_vars_dtm(df, new_vars_prefix="AST", dtc="EXSTDTC")
        assert pd.isnull(result.loc[0, "ASTDTM"])

    def test_invalid_column_raises(self):
        """ValueError raised when dtc column is missing."""
        df = pd.DataFrame({"OTHER": ["2019-07-18"]})
        with pytest.raises(ValueError, match="Column 'EXSTDTC' not found"):
            derive_vars_dtm(df, new_vars_prefix="AST", dtc="EXSTDTC")

    def test_flag_imputation_none_no_dtmf_column(self):
        """No DTMF column when flag_imputation='none'."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18"]})
        result = derive_vars_dtm(
            df,
            new_vars_prefix="AST",
            dtc="EXSTDTC",
            highest_imputation="D",
            flag_imputation="none",
        )
        assert "ASTDTMF" not in result.columns

    def test_partial_time_hhmm_imputes_seconds(self):
        """HH:MM time portion imputes seconds."""
        df = pd.DataFrame({"EXSTDTC": ["2019-07-18T15:25"]})
        result = derive_vars_dtm(
            df,
            new_vars_prefix="AST",
            dtc="EXSTDTC",
            highest_imputation="D",
            time_imputation="first",
        )
        assert result.loc[0, "ASTDTM"] == Timestamp("2019-07-18 15:25:00")
