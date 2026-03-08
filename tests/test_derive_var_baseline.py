"""Tests for derive_var_base, derive_var_chg, and derive_var_pchg."""

import pytest
import pandas as pd
import numpy as np

from admiralpy import derive_var_base, derive_var_chg, derive_var_pchg


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def bds_dataset():
    """A minimal BDS dataset with AVAL, ABLFL, and grouping variables."""
    return pd.DataFrame(
        {
            "STUDYID": ["TEST01"] * 6,
            "USUBJID": ["PAT01"] * 3 + ["PAT02"] * 3,
            "PARAMCD": ["WEIGHT"] * 6,
            "AVAL": [80.0, 80.8, 81.4, 75.3, 76.0, 77.0],
            "ABLFL": ["Y", None, None, "Y", None, None],
        }
    )


# ---------------------------------------------------------------------------
# derive_var_base
# ---------------------------------------------------------------------------


class TestDeriveVarBase:
    """Tests for derive_var_base()."""

    def test_base_derived_from_aval(self, bds_dataset):
        """BASE equals the AVAL of the ABLFL=='Y' record for each subject."""
        result = derive_var_base(
            bds_dataset, by_vars=["USUBJID", "PARAMCD"]
        )
        assert "BASE" in result.columns
        # PAT01: all three rows should get BASE = 80.0
        pat01 = result[result["USUBJID"] == "PAT01"]["BASE"].tolist()
        assert pat01 == [80.0, 80.0, 80.0]
        # PAT02: all three rows should get BASE = 75.3
        pat02 = result[result["USUBJID"] == "PAT02"]["BASE"].tolist()
        assert pat02 == [75.3, 75.3, 75.3]

    def test_custom_source_var(self, bds_dataset):
        """source_var parameter controls which column is used for baseline."""
        bds_dataset = bds_dataset.copy()
        bds_dataset["AVAL2"] = bds_dataset["AVAL"] * 2
        result = derive_var_base(
            bds_dataset,
            by_vars=["USUBJID", "PARAMCD"],
            source_var="AVAL2",
            new_var="BASE2",
        )
        assert "BASE2" in result.columns
        pat01_base = result.loc[result["USUBJID"] == "PAT01", "BASE2"].iloc[0]
        assert pat01_base == 80.0 * 2

    def test_custom_new_var(self, bds_dataset):
        """new_var parameter controls the output column name."""
        result = derive_var_base(
            bds_dataset,
            by_vars=["USUBJID", "PARAMCD"],
            new_var="MYBASE",
        )
        assert "MYBASE" in result.columns
        assert "BASE" not in result.columns

    def test_custom_filter_callable(self, bds_dataset):
        """filter_add accepts a callable that returns a boolean mask."""
        result = derive_var_base(
            bds_dataset,
            by_vars=["USUBJID", "PARAMCD"],
            filter_add=lambda df: df["ABLFL"] == "Y",
        )
        assert "BASE" in result.columns
        assert result.loc[0, "BASE"] == 80.0

    def test_custom_filter_string(self, bds_dataset):
        """filter_add accepts a pandas query string."""
        result = derive_var_base(
            bds_dataset,
            by_vars=["USUBJID", "PARAMCD"],
            filter_add='ABLFL == "Y"',
        )
        assert "BASE" in result.columns
        assert result.loc[0, "BASE"] == 80.0

    def test_missing_by_vars_raises(self, bds_dataset):
        """ValueError raised if any by_var column is absent."""
        with pytest.raises(ValueError, match="not found in dataset"):
            derive_var_base(
                bds_dataset, by_vars=["USUBJID", "NONEXISTENT"]
            )

    def test_missing_source_var_raises(self, bds_dataset):
        """ValueError raised if source_var column is absent."""
        with pytest.raises(ValueError, match="'NONEXISTENT' not found in dataset"):
            derive_var_base(
                bds_dataset,
                by_vars=["USUBJID", "PARAMCD"],
                source_var="NONEXISTENT",
            )

    def test_multiple_baseline_records_raises(self):
        """ValueError raised when multiple baseline records exist per group."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "PARAMCD": ["WEIGHT", "WEIGHT"],
                "AVAL": [80.0, 81.0],
                "ABLFL": ["Y", "Y"],
            }
        )
        with pytest.raises(ValueError, match="Multiple baseline records"):
            derive_var_base(df, by_vars=["USUBJID", "PARAMCD"])

    def test_no_baseline_record_gives_nan(self):
        """Subjects without a baseline record get NaN for BASE."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "PARAMCD": ["WEIGHT", "WEIGHT"],
                "AVAL": [80.0, 81.0],
                "ABLFL": [None, None],
            }
        )
        result = derive_var_base(df, by_vars=["USUBJID", "PARAMCD"])
        assert pd.isnull(result.loc[0, "BASE"])

    def test_original_columns_preserved(self, bds_dataset):
        """Adding BASE does not alter existing columns."""
        result = derive_var_base(
            bds_dataset, by_vars=["USUBJID", "PARAMCD"]
        )
        for col in bds_dataset.columns:
            assert col in result.columns


# ---------------------------------------------------------------------------
# derive_var_chg
# ---------------------------------------------------------------------------


class TestDeriveVarChg:
    """Tests for derive_var_chg()."""

    @pytest.fixture()
    def df_with_base(self):
        return pd.DataFrame(
            {
                "USUBJID": ["P01", "P01", "P02"],
                "PARAMCD": ["WEIGHT"] * 3,
                "AVAL": [80.0, 82.0, 76.0],
                "BASE": [80.0, 80.0, 75.0],
            }
        )

    def test_chg_computed_correctly(self, df_with_base):
        """CHG = AVAL - BASE."""
        result = derive_var_chg(df_with_base)
        assert "CHG" in result.columns
        assert result.loc[0, "CHG"] == pytest.approx(0.0)
        assert result.loc[1, "CHG"] == pytest.approx(2.0)
        assert result.loc[2, "CHG"] == pytest.approx(1.0)

    def test_chg_nan_when_base_is_nan(self):
        """CHG is NaN when BASE is NaN."""
        df = pd.DataFrame({"AVAL": [80.0], "BASE": [np.nan]})
        result = derive_var_chg(df)
        assert pd.isnull(result.loc[0, "CHG"])

    def test_chg_nan_when_aval_is_nan(self):
        """CHG is NaN when AVAL is NaN."""
        df = pd.DataFrame({"AVAL": [np.nan], "BASE": [80.0]})
        result = derive_var_chg(df)
        assert pd.isnull(result.loc[0, "CHG"])

    def test_missing_aval_raises(self):
        """ValueError raised when AVAL column is absent."""
        df = pd.DataFrame({"BASE": [80.0]})
        with pytest.raises(ValueError, match="'AVAL' not found"):
            derive_var_chg(df)

    def test_missing_base_raises(self):
        """ValueError raised when BASE column is absent."""
        df = pd.DataFrame({"AVAL": [80.0]})
        with pytest.raises(ValueError, match="'BASE' not found"):
            derive_var_chg(df)


# ---------------------------------------------------------------------------
# derive_var_pchg
# ---------------------------------------------------------------------------


class TestDeriveVarPchg:
    """Tests for derive_var_pchg()."""

    @pytest.fixture()
    def df_with_base(self):
        return pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "PARAMCD": ["WEIGHT", "WEIGHT"],
                "AVAL": [80.0, 84.0],
                "BASE": [80.0, 80.0],
            }
        )

    def test_pchg_computed_correctly(self, df_with_base):
        """PCHG = (AVAL - BASE) / |BASE| * 100."""
        result = derive_var_pchg(df_with_base)
        assert "PCHG" in result.columns
        assert result.loc[0, "PCHG"] == pytest.approx(0.0)
        assert result.loc[1, "PCHG"] == pytest.approx(5.0)

    def test_pchg_nan_when_base_is_zero(self):
        """PCHG is NaN when BASE is 0 (division by zero)."""
        df = pd.DataFrame({"AVAL": [5.0], "BASE": [0.0]})
        result = derive_var_pchg(df)
        assert pd.isnull(result.loc[0, "PCHG"])

    def test_pchg_negative_base(self):
        """PCHG uses absolute value of BASE in denominator."""
        df = pd.DataFrame({"AVAL": [-6.0], "BASE": [-10.0]})
        result = derive_var_pchg(df)
        # (AVAL - BASE) / |BASE| * 100 = (-6 - (-10)) / 10 * 100 = 40.0
        assert result.loc[0, "PCHG"] == pytest.approx(40.0)

    def test_pchg_nan_when_aval_is_nan(self):
        """PCHG is NaN when AVAL is NaN."""
        df = pd.DataFrame({"AVAL": [np.nan], "BASE": [80.0]})
        result = derive_var_pchg(df)
        assert pd.isnull(result.loc[0, "PCHG"])

    def test_missing_aval_raises(self):
        """ValueError raised when AVAL column is absent."""
        df = pd.DataFrame({"BASE": [80.0]})
        with pytest.raises(ValueError, match="'AVAL' not found"):
            derive_var_pchg(df)

    def test_missing_base_raises(self):
        """ValueError raised when BASE column is absent."""
        df = pd.DataFrame({"AVAL": [80.0]})
        with pytest.raises(ValueError, match="'BASE' not found"):
            derive_var_pchg(df)
