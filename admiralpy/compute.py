"""
Compute utility functions for common clinical trial measurements.

These functions mirror ``compute_age_years()``, ``compute_bmi()``, and
``compute_bsa()`` from the admiral R package.
"""

from typing import Union

import numpy as np
import pandas as pd

# Days per year – same constant as admiral R package
_DAYS_PER_YEAR = 365.25

# Conversion factors to years
_UNIT_TO_DAYS = {
    "years": _DAYS_PER_YEAR,
    "months": _DAYS_PER_YEAR / 12,
    "weeks": 7.0,
    "days": 1.0,
    "hours": 1.0 / 24,
    "minutes": 1.0 / (24 * 60),
    "seconds": 1.0 / (24 * 60 * 60),
}

_VALID_UNITS = set(_UNIT_TO_DAYS.keys())


def compute_age_years(
    age: Union[float, "pd.Series[float]", list],
    age_unit: Union[str, "pd.Series[str]", list],
) -> Union[float, "pd.Series[float]"]:
    """
    Convert age values from the specified time unit to years.

    Mirrors ``compute_age_years()`` from the admiral R package.  Underlying
    computations assume 365.25 days per year.

    Parameters
    ----------
    age : float, list, or pd.Series
        Age values to convert.
    age_unit : str, list, or pd.Series
        Time unit(s) for the age values.  May be a single string (applied to
        all values) or a sequence of strings (one per age value).  Values are
        case-insensitive.  Permitted values: ``"years"``, ``"months"``,
        ``"weeks"``, ``"days"``, ``"hours"``, ``"minutes"``, ``"seconds"``.
        ``None`` / ``NaN`` unit results in a ``NaN`` age.

    Returns
    -------
    float or pd.Series
        Age value(s) in years.

    Raises
    ------
    ValueError
        If any unit value is not a recognised time unit.
    ValueError
        If ``age_unit`` is a sequence whose length differs from ``age``.

    Examples
    --------
    >>> from admiralpy import compute_age_years
    >>> compute_age_years(age=24, age_unit="months")
    2.0027...
    >>> compute_age_years(age=[240, 360, 480], age_unit="months")
    [20.027..., 30.041..., 40.055...]
    >>> compute_age_years(age=[10, 520, 3650], age_unit=["years", "weeks", "days"])
    [10.0, 9.993..., 9.993...]
    """
    scalar_input = np.isscalar(age)

    # Always work with 1-D arrays internally
    age_list = [age] if scalar_input else list(age)
    age_arr = np.array(age_list, dtype=float)

    # Normalise age_unit to a 1-D array of lowercase strings / None
    if isinstance(age_unit, str) or age_unit is None or (
        not hasattr(age_unit, "__len__")
    ):
        unit_arr = np.array(
            [str(age_unit).lower() if age_unit is not None else None] * age_arr.size,
            dtype=object,
        )
    else:
        unit_arr = np.array(
            [
                str(u).lower()
                if (u is not None and not (isinstance(u, float) and np.isnan(u)))
                else None
                for u in age_unit
            ],
            dtype=object,
        )

    if unit_arr.size != age_arr.size:
        raise ValueError(
            f"age_unit must be a single string or a sequence of the same length "
            f"as age. Got {unit_arr.size} unit(s) for {age_arr.size} age(s)."
        )

    # Validate units
    bad_units = {u for u in unit_arr if u is not None and u not in _VALID_UNITS}
    if bad_units:
        raise ValueError(
            f"Unrecognised age_unit value(s): {bad_units}. "
            f"Permitted values are: {sorted(_VALID_UNITS)}."
        )

    result = np.empty(age_arr.size, dtype=float)
    for i, (a, u) in enumerate(zip(age_arr, unit_arr)):
        if u is None or np.isnan(a):
            result[i] = np.nan
        else:
            result[i] = a * _UNIT_TO_DAYS[u] / _DAYS_PER_YEAR

    if scalar_input:
        return float(result[0])
    if isinstance(age, pd.Series):
        return pd.Series(result, index=age.index)
    return result.tolist()


def compute_bmi(
    height: Union[float, "pd.Series[float]", list],
    weight: Union[float, "pd.Series[float]", list],
) -> Union[float, "pd.Series[float]"]:
    """
    Compute Body Mass Index (BMI).

    ``BMI = weight / (height / 100) ** 2``

    Mirrors ``compute_bmi()`` from the admiral R package.

    Parameters
    ----------
    height : float, list, or pd.Series
        Height in centimetres (cm).
    weight : float, list, or pd.Series
        Weight in kilograms (kg).

    Returns
    -------
    float or pd.Series
        BMI in kg/m².  Returns ``NaN`` where ``height`` is 0 or missing.

    Examples
    --------
    >>> from admiralpy import compute_bmi
    >>> compute_bmi(height=170, weight=75)
    25.95...
    >>> import pandas as pd
    >>> compute_bmi(height=pd.Series([170, 180]), weight=pd.Series([75, 90]))
    0    25.95...
    1    27.77...
    dtype: float64
    """
    scalar_input = np.isscalar(height) and np.isscalar(weight)

    h = np.asarray(height, dtype=float)
    w = np.asarray(weight, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(h == 0, np.nan, w / (h / 100.0) ** 2)

    if scalar_input:
        return float(result)
    if isinstance(height, pd.Series):
        idx = height.index
        return pd.Series(result, index=idx)
    return result.tolist()


def compute_bsa(
    height: Union[float, "pd.Series[float]", list],
    weight: Union[float, "pd.Series[float]", list],
    method: str = "mosteller",
) -> Union[float, "pd.Series[float]"]:
    """
    Compute Body Surface Area (BSA).

    Mirrors ``compute_bsa()`` from the admiral R package.

    Parameters
    ----------
    height : float, list, or pd.Series
        Height in centimetres (cm).
    weight : float, list, or pd.Series
        Weight in kilograms (kg).
    method : str, optional
        Formula to use.  One of:

        * ``"mosteller"`` – ``sqrt(height * weight / 3600)`` (default)
        * ``"dubois"``    – ``0.007184 * height^0.725 * weight^0.425``
        * ``"haycock"``   – ``0.024265 * height^0.3964 * weight^0.5378``
        * ``"gehan-george"`` – ``0.0235 * height^0.42246 * weight^0.51456``

    Returns
    -------
    float or pd.Series
        BSA in m².  Returns ``NaN`` where ``height`` or ``weight`` is
        0 or missing.

    Raises
    ------
    ValueError
        If ``method`` is not one of the recognised values.

    Examples
    --------
    >>> from admiralpy import compute_bsa
    >>> compute_bsa(height=170, weight=75)
    1.876...
    >>> compute_bsa(height=170, weight=75, method="dubois")
    1.862...
    """
    valid_methods = ("mosteller", "dubois", "haycock", "gehan-george")
    if method not in valid_methods:
        raise ValueError(
            f"method must be one of {valid_methods}, got '{method}'."
        )

    scalar_input = np.isscalar(height) and np.isscalar(weight)

    h = np.asarray(height, dtype=float)
    w = np.asarray(weight, dtype=float)

    invalid = (h == 0) | (w == 0)

    if method == "mosteller":
        result = np.sqrt(h * w / 3600.0)
    elif method == "dubois":
        result = 0.007184 * (h ** 0.725) * (w ** 0.425)
    elif method == "haycock":
        result = 0.024265 * (h ** 0.3964) * (w ** 0.5378)
    elif method == "gehan-george":
        result = 0.0235 * (h ** 0.42246) * (w ** 0.51456)

    result = np.where(invalid, np.nan, result)

    if scalar_input:
        return float(result)
    if isinstance(height, pd.Series):
        idx = height.index
        return pd.Series(result, index=idx)
    return result.tolist()
