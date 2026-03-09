"""
Functions for deriving date and datetime variables from ISO 8601 character
date/time (DTC) variables.

These functions mirror ``derive_vars_dt()`` and ``derive_vars_dtm()`` from
the admiral R package.
"""

import calendar
import re
from datetime import date, datetime
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _impute_day(year: int, month: int, date_imputation: str) -> int:
    """Return an imputed day integer for a given year/month."""
    if date_imputation == "first":
        return 1
    if date_imputation == "last":
        return calendar.monthrange(year, month)[1]
    if date_imputation == "mid":
        return 15
    # Specific date in "MM-DD" format
    if re.match(r"^\d{2}-\d{2}$", str(date_imputation)):
        return int(str(date_imputation).split("-")[1])
    return 1


def _impute_month_day(year: int, date_imputation: str) -> tuple:
    """Return (month, day) imputed values for a given year."""
    if date_imputation == "first":
        return 1, 1
    if date_imputation == "last":
        return 12, 31
    if date_imputation == "mid":
        return 6, 30
    if re.match(r"^\d{2}-\d{2}$", str(date_imputation)):
        parts = str(date_imputation).split("-")
        return int(parts[0]), int(parts[1])
    return 1, 1


def _parse_date_parts(dtc_value) -> Optional[tuple]:
    """
    Extract the date part string and time part string from a DTC value.

    Returns ``(date_str, time_str)`` or ``None`` if the value is missing.
    """
    if pd.isna(dtc_value):
        return None
    s = str(dtc_value).strip()
    if s == "":
        return None
    if "T" in s:
        date_str, _, time_str = s.partition("T")
        return date_str, time_str
    return s, None


def _parse_date_from_dtc(
    dtc_value,
    highest_imputation: str,
    date_imputation: str,
) -> tuple:
    """
    Parse a DTC value and return ``(date_or_None, imputation_flag)``.

    The imputation flag mirrors the admiral ``*DTF`` variable:

    * ``None``  – no imputation was needed
    * ``"D"``   – day was imputed
    * ``"M"``   – month (and day) were imputed
    * ``"Y"``   – year, month, and day were imputed (not yet supported)
    """
    parts = _parse_date_parts(dtc_value)
    if parts is None:
        return None, None

    date_str = parts[0]

    # YYYY-MM-DD  – complete date, no imputation required
    m_full = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", date_str)
    if m_full:
        try:
            y, mo, d = int(m_full.group(1)), int(m_full.group(2)), int(m_full.group(3))
            return date(y, mo, d), None
        except ValueError:
            return None, None

    # YYYY-MM  – missing day
    m_ym = re.match(r"^(\d{4})-(\d{2})$", date_str)
    if m_ym and highest_imputation in ("D", "M", "Y"):
        y, mo = int(m_ym.group(1)), int(m_ym.group(2))
        d = _impute_day(y, mo, date_imputation)
        try:
            return date(y, mo, d), "D"
        except ValueError:
            return None, None

    # YYYY  – missing month and day
    m_y = re.match(r"^(\d{4})$", date_str)
    if m_y and highest_imputation in ("M", "Y"):
        y = int(m_y.group(1))
        mo, d = _impute_month_day(y, date_imputation)
        try:
            return date(y, mo, d), "M"
        except ValueError:
            return None, None

    return None, None


def _parse_time_from_dtc(
    dtc_value,
    time_imputation: str,
) -> tuple:
    """
    Parse the time part of a DTC value and return ``(hour, minute, second, time_flag)``.

    ``time_flag`` mirrors the admiral ``*TMF`` variable (``"H"``, ``"M"``,
    ``"S"``, or ``None``).
    """
    parts = _parse_date_parts(dtc_value)
    if parts is None or parts[1] is None:
        # No time portion at all
        h, mi, s = _impute_time(time_imputation, level="H")
        return h, mi, s, "H"

    time_str = parts[1]

    # HH:MM:SS
    m_full = re.match(r"^(\d{2}):(\d{2}):(\d{2})$", time_str)
    if m_full:
        return int(m_full.group(1)), int(m_full.group(2)), int(m_full.group(3)), None

    # HH:MM  – missing seconds
    m_hm = re.match(r"^(\d{2}):(\d{2})$", time_str)
    if m_hm:
        h, mi = int(m_hm.group(1)), int(m_hm.group(2))
        s = _impute_time_component(time_imputation, level="S")
        return h, mi, s, "S"

    # HH  – missing minutes and seconds
    m_h = re.match(r"^(\d{2})$", time_str)
    if m_h:
        h = int(m_h.group(1))
        mi = _impute_time_component(time_imputation, level="M")
        s = _impute_time_component(time_imputation, level="S")
        return h, mi, s, "M"

    return 0, 0, 0, "H"


def _impute_time(time_imputation: str, level: str) -> tuple:
    """Return ``(hour, minute, second)`` for a fully-imputed time."""
    if time_imputation == "first":
        return 0, 0, 0
    if time_imputation == "last":
        return 23, 59, 59
    return 0, 0, 0


def _impute_time_component(time_imputation: str, level: str) -> int:
    """Return a single imputed time component (minute or second)."""
    if time_imputation == "first":
        return 0
    if time_imputation == "last":
        return 59
    return 0


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def derive_vars_dt(
    dataset: pd.DataFrame,
    new_vars_prefix: str,
    dtc: str,
    highest_imputation: str = "n",
    date_imputation: str = "first",
    flag_imputation: str = "auto",
) -> pd.DataFrame:
    """
    Derive a date variable (``*DT``) from a character date variable (``--DTC``).

    Mirrors ``derive_vars_dt()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset. Must contain the column named by ``dtc``.
    new_vars_prefix : str
        Prefix for the output variables.  For example, ``"AST"`` creates
        ``ASTDT`` (and ``ASTDTF`` when the imputation flag is requested).
    dtc : str
        Name of the source character date variable.
    highest_imputation : str, optional
        Highest imputation level allowed.  One of:

        * ``"n"`` – no imputation (default)
        * ``"D"`` – impute missing day
        * ``"M"`` – impute missing month and/or day
        * ``"Y"`` – impute missing year, month, and/or day
    date_imputation : str, optional
        How to impute missing date components.  One of:

        * ``"first"`` – first day/month (default)
        * ``"last"``  – last day/month
        * ``"mid"``   – mid day/month (15th for day, 30 Jun for month)
        * ``"MM-DD"`` – a specific month-day string, e.g. ``"06-15"``
    flag_imputation : str, optional
        Controls creation of the date imputation flag ``*DTF``.  One of:

        * ``"auto"``  – create flag when ``highest_imputation != "n"`` (default)
        * ``"date"``  – always create flag
        * ``"none"``  – never create flag

    Returns
    -------
    pd.DataFrame
        Input dataset with ``{new_vars_prefix}DT`` (and optionally
        ``{new_vars_prefix}DTF``) appended.

    Raises
    ------
    ValueError
        If ``dtc`` is not present in ``dataset`` or if ``highest_imputation``
        is not a recognised value.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_vars_dt
    >>> df = pd.DataFrame({
    ...     "MHSTDTC": ["2019-07-18T15:25:40", "2019-07-18", "2019-02", "2019", ""]
    ... })
    >>> derive_vars_dt(df, new_vars_prefix="AST", dtc="MHSTDTC",
    ...                highest_imputation="M", date_imputation="first")
    """
    if dtc not in dataset.columns:
        raise ValueError(f"Column '{dtc}' not found in dataset.")

    valid_highest = ("n", "D", "M", "Y")
    if highest_imputation not in valid_highest:
        raise ValueError(
            f"highest_imputation must be one of {valid_highest}, "
            f"got '{highest_imputation}'."
        )

    dt_var = f"{new_vars_prefix}DT"
    dtf_var = f"{new_vars_prefix}DTF"

    derive_flag = flag_imputation == "date" or (
        flag_imputation == "auto" and highest_imputation != "n"
    )

    dates = []
    flags = []

    for val in dataset[dtc]:
        parsed_date, imputation_flag = _parse_date_from_dtc(
            val, highest_imputation, date_imputation
        )
        dates.append(
            pd.NaT if parsed_date is None else pd.Timestamp(parsed_date)
        )
        flags.append(imputation_flag)

    result = dataset.copy()
    result[dt_var] = pd.array(dates, dtype="datetime64[ns]")

    if derive_flag:
        result[dtf_var] = flags

    return result


def derive_vars_dtm(
    dataset: pd.DataFrame,
    new_vars_prefix: str,
    dtc: str,
    highest_imputation: str = "n",
    date_imputation: str = "first",
    time_imputation: str = "first",
    flag_imputation: str = "auto",
) -> pd.DataFrame:
    """
    Derive a datetime variable (``*DTM``) from a character datetime variable (``--DTC``).

    Mirrors ``derive_vars_dtm()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset. Must contain the column named by ``dtc``.
    new_vars_prefix : str
        Prefix for the output variables.  For example, ``"AST"`` creates
        ``ASTDTM`` (and ``ASTDTMF`` when the imputation flag is requested).
    dtc : str
        Name of the source character datetime variable.
    highest_imputation : str, optional
        Highest imputation level allowed for the date part.  One of:

        * ``"n"`` – no imputation (default)
        * ``"D"`` – impute missing day
        * ``"M"`` – impute missing month and/or day
        * ``"Y"`` – impute missing year, month, and/or day
    date_imputation : str, optional
        How to impute missing date components (``"first"``, ``"last"``,
        ``"mid"``, or ``"MM-DD"``).  Default is ``"first"``.
    time_imputation : str, optional
        How to impute missing time components.  One of:

        * ``"first"`` – ``00:00:00`` (default)
        * ``"last"``  – ``23:59:59``
    flag_imputation : str, optional
        Controls creation of the imputation flag ``*DTMF``.  One of:

        * ``"auto"``  – create flag when any imputation occurs (default)
        * ``"datetime"`` – always create flag
        * ``"none"``  – never create flag

    Returns
    -------
    pd.DataFrame
        Input dataset with ``{new_vars_prefix}DTM`` (and optionally
        ``{new_vars_prefix}DTMF``) appended.

    Raises
    ------
    ValueError
        If ``dtc`` is not present in ``dataset`` or if ``highest_imputation``
        is not a recognised value.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_vars_dtm
    >>> df = pd.DataFrame({
    ...     "EXSTDTC": ["2019-07-18T15:25:40", "2019-07-18T15:25", "2019-07-18", ""]
    ... })
    >>> derive_vars_dtm(df, new_vars_prefix="AST", dtc="EXSTDTC",
    ...                 highest_imputation="D", time_imputation="first")
    """
    if dtc not in dataset.columns:
        raise ValueError(f"Column '{dtc}' not found in dataset.")

    valid_highest = ("n", "D", "M", "Y")
    if highest_imputation not in valid_highest:
        raise ValueError(
            f"highest_imputation must be one of {valid_highest}, "
            f"got '{highest_imputation}'."
        )

    dtm_var = f"{new_vars_prefix}DTM"
    dtmf_var = f"{new_vars_prefix}DTMF"

    derive_flag = flag_imputation in ("datetime",) or (
        flag_imputation == "auto" and highest_imputation != "n"
    )

    datetimes = []
    flags = []

    for val in dataset[dtc]:
        parsed_date, date_flag = _parse_date_from_dtc(
            val, highest_imputation, date_imputation
        )
        if parsed_date is None:
            datetimes.append(pd.NaT)
            flags.append(None)
            continue

        h, mi, s, time_flag = _parse_time_from_dtc(val, time_imputation)

        datetimes.append(
            pd.Timestamp(
                year=parsed_date.year,
                month=parsed_date.month,
                day=parsed_date.day,
                hour=h,
                minute=mi,
                second=s,
            )
        )
        # Combine flags: report the 'higher-priority' imputation
        combined_flag = date_flag or time_flag
        flags.append(combined_flag)

    result = dataset.copy()
    result[dtm_var] = pd.array(datetimes, dtype="datetime64[ns]")

    if derive_flag:
        result[dtmf_var] = flags

    return result
