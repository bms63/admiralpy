"""Tests for derive_param_computed."""

import pytest
import pandas as pd
import numpy as np

from admiralpy import derive_param_computed


@pytest.fixture()
def advs():
    """Minimal BDS dataset with SYSBP and DIABP."""
    return pd.DataFrame(
        {
            "USUBJID": ["P01", "P01", "P01", "P01"],
            "AVISIT":  ["BASELINE", "BASELINE", "WEEK 2", "WEEK 2"],
            "AVISITN": [0, 0, 2, 2],
            "PARAMCD": ["SYSBP", "DIABP", "SYSBP", "DIABP"],
            "PARAM": [
                "Systolic Blood Pressure (mmHg)",
                "Diastolic Blood Pressure (mmHg)",
                "Systolic Blood Pressure (mmHg)",
                "Diastolic Blood Pressure (mmHg)",
            ],
            "AVAL":    [120.0, 80.0, 118.0, 78.0],
        }
    )


class TestDeriveParamComputed:
    def test_map_formula(self, advs):
        """MAP = (SYSBP + 2*DIABP) / 3 is computed correctly."""
        result = derive_param_computed(
            advs,
            by_vars=["USUBJID", "AVISIT", "AVISITN"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={
                "AVAL": lambda w: (w["AVAL_SYSBP"] + 2 * w["AVAL_DIABP"]) / 3,
                "PARAMCD": "MAP",
                "PARAM": "Mean Arterial Pressure (mmHg)",
            },
        )
        map_rows = result[result["PARAMCD"] == "MAP"]
        assert len(map_rows) == 2  # one per visit

        baseline_map = map_rows[map_rows["AVISIT"] == "BASELINE"]["AVAL"].iloc[0]
        expected = (120.0 + 2 * 80.0) / 3
        assert baseline_map == pytest.approx(expected)

    def test_new_rows_appended(self, advs):
        """Original rows are preserved and new rows are appended."""
        result = derive_param_computed(
            advs,
            by_vars=["USUBJID", "AVISIT"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={"AVAL": lambda w: w["AVAL_SYSBP"] + w["AVAL_DIABP"],
                           "PARAMCD": "SUM"},
        )
        assert len(result) == len(advs) + 2

    def test_constant_paramcd_set(self, advs):
        """PARAMCD is set as a constant string in new rows."""
        result = derive_param_computed(
            advs,
            by_vars=["USUBJID", "AVISIT"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={"AVAL": lambda w: w["AVAL_SYSBP"],
                           "PARAMCD": "TESTPARAM"},
        )
        new_rows = result[result["PARAMCD"] == "TESTPARAM"]
        assert (new_rows["PARAMCD"] == "TESTPARAM").all()

    def test_non_by_vars_set_to_nan_in_new_rows(self, advs):
        """Variables not in by_vars / set_values_to are NaN in new rows."""
        result = derive_param_computed(
            advs,
            by_vars=["USUBJID", "AVISIT"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={"AVAL": lambda w: w["AVAL_SYSBP"], "PARAMCD": "TST"},
        )
        new_rows = result[result["PARAMCD"] == "TST"]
        # AVISITN is not in by_vars here, so should be NaN
        assert new_rows["AVISITN"].isna().all()

    def test_keep_nas_false_drops_nan_groups(self):
        """Groups with NaN contributing values are skipped when keep_nas=False."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "AVISIT":  ["BASELINE", "BASELINE"],
                "PARAMCD": ["SYSBP", "DIABP"],
                "AVAL":    [120.0, np.nan],
            }
        )
        result = derive_param_computed(
            df,
            by_vars=["USUBJID", "AVISIT"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={"AVAL": lambda w: w["AVAL_SYSBP"] + w["AVAL_DIABP"],
                           "PARAMCD": "SUM"},
            keep_nas=False,
        )
        assert "SUM" not in result["PARAMCD"].values

    def test_keep_nas_true_includes_nan_groups(self):
        """keep_nas=True allows NaN groups to generate a new row."""
        df = pd.DataFrame(
            {
                "USUBJID": ["P01", "P01"],
                "AVISIT":  ["BASELINE", "BASELINE"],
                "PARAMCD": ["SYSBP", "DIABP"],
                "AVAL":    [120.0, np.nan],
            }
        )
        result = derive_param_computed(
            df,
            by_vars=["USUBJID", "AVISIT"],
            parameters=["SYSBP", "DIABP"],
            set_values_to={
                "AVAL": lambda w: w["AVAL_SYSBP"],
                "PARAMCD": "SUM",
            },
            keep_nas=True,
        )
        assert "SUM" in result["PARAMCD"].values

    def test_missing_paramcd_raises(self, advs):
        """ValueError raised when PARAMCD column is absent."""
        df = advs.drop(columns=["PARAMCD"])
        with pytest.raises(ValueError, match="PARAMCD"):
            derive_param_computed(df, by_vars=["USUBJID"], parameters=["SYSBP"],
                                  set_values_to={"PARAMCD": "MAP"})

    def test_missing_by_var_raises(self, advs):
        """ValueError raised when a by_var column is absent."""
        with pytest.raises(ValueError, match="not found in dataset"):
            derive_param_computed(advs, by_vars=["NONEXISTENT"],
                                  parameters=["SYSBP"],
                                  set_values_to={"PARAMCD": "MAP"})
