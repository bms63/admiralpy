"""Tests for filter_extreme."""

import pytest
import pandas as pd
import numpy as np
import warnings

from admiralpy import filter_extreme


@pytest.fixture()
def advs_map():
    return pd.DataFrame(
        {
            "USUBJID": ["P01", "P01", "P01", "P02", "P02"],
            "PARAMCD": ["MAP", "MAP", "MAP", "MAP", "MAP"],
            "AVISITN": [0, 2, 4, 0, 4],
            "AVAL":    [93.0, 91.5, 94.0, 88.0, 89.0],
        }
    )


class TestFilterExtreme:
    def test_last_visit_per_subject(self, advs_map):
        """mode='last' returns the last record per by group."""
        result = filter_extreme(
            advs_map,
            by_vars=["USUBJID"],
            order=["AVISITN"],
            mode="last",
        )
        assert len(result) == 2
        assert result.loc[result["USUBJID"] == "P01", "AVISITN"].iloc[0] == 4
        assert result.loc[result["USUBJID"] == "P02", "AVISITN"].iloc[0] == 4

    def test_first_visit_per_subject(self, advs_map):
        """mode='first' returns the first record per by group."""
        result = filter_extreme(
            advs_map,
            by_vars=["USUBJID"],
            order=["AVISITN"],
            mode="first",
        )
        assert len(result) == 2
        assert result.loc[result["USUBJID"] == "P01", "AVISITN"].iloc[0] == 0

    def test_no_by_vars_returns_single_row(self, advs_map):
        """Without by_vars the whole dataset is treated as one group."""
        result = filter_extreme(advs_map, order=["AVISITN"], mode="first")
        assert len(result) == 1
        assert result["AVISITN"].iloc[0] == 0

    def test_descending_order_prefix(self, advs_map):
        """Prefix '-' on order column gives descending sort."""
        result = filter_extreme(
            advs_map,
            by_vars=["USUBJID"],
            order=["-AVISITN"],
            mode="first",
        )
        # first after descending sort → last visit
        assert result.loc[result["USUBJID"] == "P01", "AVISITN"].iloc[0] == 4

    def test_original_column_order_preserved(self, advs_map):
        """Output columns appear in the same order as the input."""
        result = filter_extreme(
            advs_map, by_vars=["USUBJID"], order=["AVISITN"], mode="last"
        )
        assert list(result.columns) == list(advs_map.columns)

    def test_invalid_mode_raises(self, advs_map):
        with pytest.raises(ValueError, match="mode must be"):
            filter_extreme(advs_map, order=["AVISITN"], mode="middle")

    def test_missing_by_var_raises(self, advs_map):
        with pytest.raises(ValueError, match="not found in dataset"):
            filter_extreme(advs_map, by_vars=["NONEXISTENT"],
                           order=["AVISITN"], mode="first")

    def test_missing_order_col_raises(self, advs_map):
        with pytest.raises(ValueError, match="not found in dataset"):
            filter_extreme(advs_map, by_vars=["USUBJID"],
                           order=["NONEXISTENT"], mode="first")

    def test_check_type_warning_on_duplicates(self):
        """check_type='warning' issues a UserWarning for duplicate records."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "AVISITN": [0, 0],  # duplicates within by+order key
                "AVAL":    [93.0, 93.0],
            }
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            filter_extreme(df, by_vars=["USUBJID"], order=["AVISITN"],
                           mode="first", check_type="warning")
            duplicate_warnings = [
                x for x in w
                if issubclass(x.category, UserWarning)
                and "Duplicate records" in str(x.message)
            ]
            assert len(duplicate_warnings) >= 1

    def test_check_type_none_suppresses_warning(self):
        """check_type='none' does not issue any warning."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "AVISITN": [0, 0],
                "AVAL":    [93.0, 93.0],
            }
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            filter_extreme(df, by_vars=["USUBJID"], order=["AVISITN"],
                           mode="first", check_type="none")
            assert len(w) == 0
