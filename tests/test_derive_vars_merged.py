"""Tests for derive_vars_merged."""

import pytest
import pandas as pd
import numpy as np

from admiralpy import derive_vars_merged


@pytest.fixture()
def adsl():
    return pd.DataFrame(
        {
            "STUDYID": ["S01", "S01", "S01"],
            "USUBJID": ["P01", "P02", "P03"],
            "AGE": [30, 40, 50],
        }
    )


@pytest.fixture()
def ex():
    return pd.DataFrame(
        {
            "STUDYID": ["S01", "S01", "S01", "S01"],
            "USUBJID": ["P01", "P01", "P02", "P03"],
            "EXSTDTC": ["2020-01-01", "2020-02-01", "2020-01-15", "2020-03-01"],
            "EXSEQ": [1, 2, 1, 1],
            "EXTRT": ["DRUG", "DRUG", "DRUG", "PLACEBO"],
        }
    )


class TestDeriveVarsMerged:
    def test_basic_merge_all_new_vars(self, adsl, ex):
        """Without new_vars, columns from dataset_add are merged (with dedup via order/mode)."""
        result = derive_vars_merged(adsl, ex, by_vars=["USUBJID"],
                                    order=["EXSEQ"], mode="first")
        assert "EXSTDTC" in result.columns
        assert "EXSEQ" in result.columns
        assert len(result) == 3

    def test_merge_with_new_vars_rename(self, adsl, ex):
        """new_vars renames source column to new column name."""
        result = derive_vars_merged(
            adsl, ex, by_vars=["USUBJID"],
            new_vars={"TRTSTDTC": "EXSTDTC"},
        )
        assert "TRTSTDTC" in result.columns
        assert "EXSTDTC" not in result.columns

    def test_order_mode_first(self, adsl, ex):
        """mode='first' selects the earliest record per group."""
        result = derive_vars_merged(
            adsl, ex, by_vars=["USUBJID"],
            new_vars={"TRTSTDTC": "EXSTDTC"},
            order=["EXSEQ"],
            mode="first",
        )
        assert result.loc[result["USUBJID"] == "P01", "TRTSTDTC"].iloc[0] == "2020-01-01"

    def test_order_mode_last(self, adsl, ex):
        """mode='last' selects the latest record per group."""
        result = derive_vars_merged(
            adsl, ex, by_vars=["USUBJID"],
            new_vars={"TRTSTDTC": "EXSTDTC"},
            order=["EXSEQ"],
            mode="last",
        )
        assert result.loc[result["USUBJID"] == "P01", "TRTSTDTC"].iloc[0] == "2020-02-01"

    def test_filter_add_string(self, adsl, ex):
        """filter_add (string) filters dataset_add before merging."""
        result = derive_vars_merged(
            adsl, ex, by_vars=["USUBJID"],
            new_vars={"TRTCD": "EXTRT"},
            filter_add='EXTRT == "PLACEBO"',
        )
        assert result.loc[result["USUBJID"] == "P03", "TRTCD"].iloc[0] == "PLACEBO"
        # P01 and P02 have no PLACEBO records → NaN
        assert pd.isna(result.loc[result["USUBJID"] == "P01", "TRTCD"].iloc[0])

    def test_filter_add_callable(self, adsl, ex):
        """filter_add (callable) filters dataset_add before merging."""
        result = derive_vars_merged(
            adsl, ex, by_vars=["USUBJID"],
            new_vars={"TRTCD": "EXTRT"},
            filter_add=lambda df: df["EXTRT"] == "PLACEBO",
        )
        assert result.loc[result["USUBJID"] == "P03", "TRTCD"].iloc[0] == "PLACEBO"

    def test_missing_by_var_in_dataset_raises(self, adsl, ex):
        with pytest.raises(ValueError, match="not found in dataset"):
            derive_vars_merged(adsl, ex, by_vars=["NONEXISTENT"])

    def test_missing_by_var_in_dataset_add_raises(self, adsl, ex):
        adsl2 = adsl.rename(columns={"USUBJID": "SUBJID"})
        with pytest.raises(ValueError, match="not found in dataset_add"):
            derive_vars_merged(adsl2, ex, by_vars=["SUBJID"])

    def test_mode_without_order_raises(self, adsl, ex):
        with pytest.raises(ValueError, match="Both 'order' and 'mode' must be specified"):
            derive_vars_merged(adsl, ex, by_vars=["USUBJID"], mode="first")

    def test_missing_source_column_in_new_vars_raises(self, adsl, ex):
        with pytest.raises(ValueError, match="Source column 'NONEXISTENT' not found"):
            derive_vars_merged(
                adsl, ex, by_vars=["USUBJID"],
                new_vars={"X": "NONEXISTENT"},
            )

    def test_left_join_preserves_all_input_rows(self, adsl, ex):
        """All rows from dataset are kept even when dataset_add has no match."""
        extra = adsl.copy()
        extra.loc[3] = {"STUDYID": "S01", "USUBJID": "P99", "AGE": 99}
        result = derive_vars_merged(extra, ex, by_vars=["USUBJID"],
                                    new_vars={"TRTSTDTC": "EXSTDTC"},
                                    order=["EXSEQ"], mode="first")
        assert len(result) == 4
        assert pd.isna(result.loc[result["USUBJID"] == "P99", "TRTSTDTC"].iloc[0])
