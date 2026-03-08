"""
Computation functions for converting between date/time representations.

These functions mirror ``convert_dtc_to_dt()`` and ``convert_dtc_to_dtm()``
from the admiral R package.
"""

import re
from datetime import date, datetime
from typing import Optional, Union

import pandas as pd

from admiralpy.derive_vars_dt import _parse_date_from_dtc


def convert_dtc_to_dt(
    dtc: Union[str, pd.Series],
    highest_imputation: str = "n",
    date_imputation: str = "first",
) -> Union[Optional[date], pd.Series]:
    """
    Convert an ISO 8601 character date (DTC) to a :class:`datetime.date`.

    This is a vectorised computation function — it can be applied element-wise
    inside :func:`pandas.DataFrame.assign` / ``mutate()``-style calls or passed
    as a scalar.

    Mirrors ``convert_dtc_to_dt()`` from the admiral R package.

    Parameters
    ----------
    dtc : str or pd.Series
        ISO 8601 character date string(s), e.g. ``"2019-07-18"`` or
        ``"2019-07-18T15:25:40"``.
    highest_imputation : str, optional
        Highest imputation level.  Same semantics as
        :func:`~admiralpy.derive_vars_dt.derive_vars_dt`.  Default is ``"n"``
        (no imputation).
    date_imputation : str, optional
        Imputation strategy for missing date components (``"first"``,
        ``"last"``, ``"mid"``, or ``"MM-DD"``).  Default is ``"first"``.

    Returns
    -------
    datetime.date or None, or pd.Series
        Converted date(s).  ``None`` / ``NaT`` for missing or un-parseable
        values.

    Examples
    --------
    >>> from admiralpy import convert_dtc_to_dt
    >>> convert_dtc_to_dt("2019-07-18")
    datetime.date(2019, 7, 18)
    >>> convert_dtc_to_dt("2019-07-18T15:25:40")
    datetime.date(2019, 7, 18)
    >>> import pandas as pd
    >>> s = pd.Series(["2019-07-18", "2020-01-01", ""])
    >>> convert_dtc_to_dt(s)
    0   2019-07-18
    1   2020-01-01
    2          NaT
    dtype: datetime64[ns]
    """
    if isinstance(dtc, pd.Series):
        results = []
        for val in dtc:
            parsed, _ = _parse_date_from_dtc(val, highest_imputation, date_imputation)
            results.append(pd.NaT if parsed is None else pd.Timestamp(parsed))
        return pd.Series(results, index=dtc.index, dtype="datetime64[ns]")

    # Scalar path
    parsed, _ = _parse_date_from_dtc(dtc, highest_imputation, date_imputation)
    return parsed


def convert_dtc_to_dtm(
    dtc: Union[str, pd.Series],
    highest_imputation: str = "n",
    date_imputation: str = "first",
    time_imputation: str = "first",
) -> Union[Optional[datetime], pd.Series]:
    """
    Convert an ISO 8601 character datetime (DTC) to a :class:`datetime.datetime`.

    Mirrors ``convert_dtc_to_dtm()`` from the admiral R package.

    Parameters
    ----------
    dtc : str or pd.Series
        ISO 8601 datetime string(s).
    highest_imputation : str, optional
        Highest date imputation level (default ``"n"``).
    date_imputation : str, optional
        Date imputation strategy (default ``"first"``).
    time_imputation : str, optional
        Time imputation strategy (``"first"`` or ``"last"``).
        Default is ``"first"`` (``00:00:00``).

    Returns
    -------
    datetime.datetime or None, or pd.Series
        Converted datetime(s).  ``None`` / ``NaT`` for missing values.

    Examples
    --------
    >>> from admiralpy import convert_dtc_to_dtm
    >>> convert_dtc_to_dtm("2019-07-18T15:25:40")
    datetime.datetime(2019, 7, 18, 15, 25, 40)
    >>> convert_dtc_to_dtm("2019-07-18", highest_imputation="D",
    ...                     time_imputation="last")
    datetime.datetime(2019, 7, 18, 23, 59, 59)
    """
    from admiralpy.derive_vars_dt import _parse_date_from_dtc, _parse_time_from_dtc

    def _convert_one(val):
        parsed_date, _ = _parse_date_from_dtc(val, highest_imputation, date_imputation)
        if parsed_date is None:
            return None
        h, mi, s, _ = _parse_time_from_dtc(val, time_imputation)
        return datetime(parsed_date.year, parsed_date.month, parsed_date.day, h, mi, s)

    if isinstance(dtc, pd.Series):
        results = [_convert_one(v) for v in dtc]
        return pd.Series(
            [pd.NaT if r is None else pd.Timestamp(r) for r in results],
            index=dtc.index,
            dtype="datetime64[ns]",
        )

    return _convert_one(dtc)
