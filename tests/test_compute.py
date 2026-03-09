"""Tests for compute_age_years, compute_bmi, and compute_bsa."""

import pytest
import pandas as pd
import numpy as np

from admiralpy import compute_age_years, compute_bmi, compute_bsa


# ---------------------------------------------------------------------------
# compute_age_years
# ---------------------------------------------------------------------------


class TestComputeAgeYears:
    """Tests for compute_age_years()."""

    def test_years_unchanged(self):
        """Age in years is returned as-is."""
        assert compute_age_years(30, "years") == pytest.approx(30.0)

    def test_months_to_years(self):
        """12 months ≈ 1 year."""
        result = compute_age_years(12, "months")
        assert result == pytest.approx(12 / 12)

    def test_weeks_to_years(self):
        """52 weeks ≈ 1 year (365.25 days / 7)."""
        result = compute_age_years(52, "weeks")
        expected = 52 * 7 / 365.25
        assert result == pytest.approx(expected, rel=1e-4)

    def test_days_to_years(self):
        """365.25 days = 1 year."""
        result = compute_age_years(365.25, "days")
        assert result == pytest.approx(1.0)

    def test_hours_to_years(self):
        """24 * 365.25 hours = 1 year."""
        result = compute_age_years(24 * 365.25, "hours")
        assert result == pytest.approx(1.0)

    def test_minutes_to_years(self):
        """60 * 24 * 365.25 minutes = 1 year."""
        result = compute_age_years(60 * 24 * 365.25, "minutes")
        assert result == pytest.approx(1.0)

    def test_seconds_to_years(self):
        """3600 * 24 * 365.25 seconds = 1 year."""
        result = compute_age_years(3600 * 24 * 365.25, "seconds")
        assert result == pytest.approx(1.0)

    def test_case_insensitive_units(self):
        """Unit strings are case-insensitive."""
        assert compute_age_years(12, "MONTHS") == pytest.approx(
            compute_age_years(12, "months")
        )
        assert compute_age_years(365.25, "DAYS") == pytest.approx(
            compute_age_years(365.25, "days")
        )

    def test_vector_input_single_unit(self):
        """List of ages with a single unit string."""
        result = compute_age_years([12, 24, 36], "months")
        assert isinstance(result, list)
        assert result[0] == pytest.approx(12 / 12)
        assert result[1] == pytest.approx(24 / 12)
        assert result[2] == pytest.approx(36 / 12)

    def test_vector_input_vector_units(self):
        """List of ages with matching list of units."""
        result = compute_age_years([10, 365.25, 52], ["years", "days", "weeks"])
        assert result[0] == pytest.approx(10.0)
        assert result[1] == pytest.approx(1.0)
        assert result[2] == pytest.approx(52 * 7 / 365.25, rel=1e-4)

    def test_nan_unit_returns_nan(self):
        """None/NaN unit produces NaN age."""
        result = compute_age_years(10, None)
        assert np.isnan(result)

    def test_vector_with_none_unit(self):
        """None unit in a list of units gives NaN for that element."""
        result = compute_age_years([10, 365.25], ["years", None])
        assert result[0] == pytest.approx(10.0)
        assert np.isnan(result[1])

    def test_invalid_unit_raises(self):
        """ValueError raised for unrecognised unit."""
        with pytest.raises(ValueError, match="Unrecognised age_unit"):
            compute_age_years(10, "fortnights")

    def test_mismatched_lengths_raises(self):
        """ValueError raised when age and age_unit lengths differ."""
        with pytest.raises(ValueError, match="same length"):
            compute_age_years([10, 20], ["years", "months", "days"])

    def test_series_input_returns_series(self):
        """pd.Series input returns pd.Series output."""
        age = pd.Series([12, 24])
        result = compute_age_years(age, "months")
        assert isinstance(result, pd.Series)
        assert result.iloc[0] == pytest.approx(1.0)

    def test_scalar_input_returns_float(self):
        """Scalar input returns a Python float."""
        result = compute_age_years(365.25, "days")
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# compute_bmi
# ---------------------------------------------------------------------------


class TestComputeBmi:
    """Tests for compute_bmi()."""

    def test_known_value(self):
        """BMI = weight / (height/100)^2."""
        result = compute_bmi(height=170, weight=70)
        expected = 70 / (170 / 100) ** 2
        assert result == pytest.approx(expected)

    def test_zero_height_returns_nan(self):
        """Zero height produces NaN."""
        result = compute_bmi(height=0, weight=70)
        assert np.isnan(result)

    def test_vector_input(self):
        """Vector inputs produce a list of BMI values."""
        result = compute_bmi(height=[170, 180], weight=[70, 90])
        assert isinstance(result, list)
        assert result[0] == pytest.approx(70 / (170 / 100) ** 2)
        assert result[1] == pytest.approx(90 / (180 / 100) ** 2)

    def test_series_input_returns_series(self):
        """pd.Series inputs return a pd.Series."""
        h = pd.Series([170.0, 180.0])
        w = pd.Series([70.0, 90.0])
        result = compute_bmi(h, w)
        assert isinstance(result, pd.Series)

    def test_scalar_returns_float(self):
        """Scalar input returns a Python float."""
        result = compute_bmi(170, 70)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# compute_bsa
# ---------------------------------------------------------------------------


class TestComputeBsa:
    """Tests for compute_bsa()."""

    def test_mosteller_formula(self):
        """Mosteller BSA = sqrt(height * weight / 3600)."""
        result = compute_bsa(height=170, weight=70, method="mosteller")
        expected = (170 * 70 / 3600) ** 0.5
        assert result == pytest.approx(expected)

    def test_dubois_formula(self):
        """DuBois BSA = 0.007184 * h^0.725 * w^0.425."""
        result = compute_bsa(height=170, weight=70, method="dubois")
        expected = 0.007184 * (170 ** 0.725) * (70 ** 0.425)
        assert result == pytest.approx(expected)

    def test_haycock_formula(self):
        """Haycock BSA = 0.024265 * h^0.3964 * w^0.5378."""
        result = compute_bsa(height=170, weight=70, method="haycock")
        expected = 0.024265 * (170 ** 0.3964) * (70 ** 0.5378)
        assert result == pytest.approx(expected)

    def test_gehan_george_formula(self):
        """Gehan-George BSA = 0.0235 * h^0.42246 * w^0.51456."""
        result = compute_bsa(height=170, weight=70, method="gehan-george")
        expected = 0.0235 * (170 ** 0.42246) * (70 ** 0.51456)
        assert result == pytest.approx(expected)

    def test_default_method_is_mosteller(self):
        """Default method is 'mosteller'."""
        default = compute_bsa(170, 70)
        mosteller = compute_bsa(170, 70, method="mosteller")
        assert default == pytest.approx(mosteller)

    def test_zero_height_returns_nan(self):
        """Zero height produces NaN."""
        result = compute_bsa(height=0, weight=70)
        assert np.isnan(result)

    def test_zero_weight_returns_nan(self):
        """Zero weight produces NaN."""
        result = compute_bsa(height=170, weight=0)
        assert np.isnan(result)

    def test_invalid_method_raises(self):
        """ValueError raised for unrecognised method."""
        with pytest.raises(ValueError, match="method must be one of"):
            compute_bsa(height=170, weight=70, method="invalid")

    def test_vector_input(self):
        """Vector inputs produce a list of BSA values."""
        result = compute_bsa(height=[170, 180], weight=[70, 90])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_series_input_returns_series(self):
        """pd.Series inputs return a pd.Series."""
        h = pd.Series([170.0, 180.0])
        w = pd.Series([70.0, 90.0])
        result = compute_bsa(h, w)
        assert isinstance(result, pd.Series)

    def test_scalar_returns_float(self):
        """Scalar input returns a Python float."""
        result = compute_bsa(170, 70)
        assert isinstance(result, float)

    def test_bsa_reasonable_range(self):
        """BSA for average adult is roughly 1.5–2.2 m²."""
        result = compute_bsa(175, 75)
        assert 1.5 < result < 2.2
