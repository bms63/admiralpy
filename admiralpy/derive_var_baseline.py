"""
Functions for deriving baseline and change-from-baseline variables in BDS
(Basic Data Structure) datasets.

These functions mirror ``derive_var_base()``, ``derive_var_chg()``, and
``derive_var_pchg()`` from the admiral R package.
"""

from typing import Callable, List, Optional, Union

import numpy as np
import pandas as pd


def derive_var_base(
    dataset: pd.DataFrame,
    by_vars: List[str],
    source_var: str = "AVAL",
    new_var: str = "BASE",
    filter_add: Optional[Union[str, Callable]] = None,
) -> pd.DataFrame:
    """
    Derive a baseline variable in a BDS dataset.

    For each group defined by ``by_vars``, the baseline record is identified
    (by default the record where ``ABLFL == "Y"``). The value of
    ``source_var`` from that record is then merged back to all records in the
    group as ``new_var``.

    Mirrors ``derive_var_base()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset. Must contain the columns specified in ``by_vars`` and
        ``source_var``.
    by_vars : list of str
        Grouping variables that uniquely identify each subject/parameter
        combination (e.g. ``["USUBJID", "PARAMCD"]``).
    source_var : str, optional
        Column from which to extract the baseline value. Default is ``"AVAL"``.
    new_var : str, optional
        Name of the new baseline column. Default is ``"BASE"``.
    filter_add : str or callable, optional
        Condition used to identify baseline records.

        * If a **string**, it is passed to :meth:`pandas.DataFrame.query`.
          Default string is ``'ABLFL == "Y"'``.
        * If a **callable**, it receives the dataset and returns a boolean
          Series.
        * If ``None``, defaults to ``'ABLFL == "Y"'``.

    Returns
    -------
    pd.DataFrame
        Input dataset with ``new_var`` appended.

    Raises
    ------
    ValueError
        If ``by_vars`` or ``source_var`` are missing from ``dataset``.
    ValueError
        If more than one baseline record exists per ``by_vars`` group.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_var_base
    >>> df = pd.DataFrame({
    ...     "USUBJID": ["P01", "P01", "P01"],
    ...     "PARAMCD": ["WEIGHT", "WEIGHT", "WEIGHT"],
    ...     "AVAL":    [80.0, 80.8, 81.4],
    ...     "ABLFL":   ["Y", None, None],
    ... })
    >>> derive_var_base(df, by_vars=["USUBJID", "PARAMCD"])
    """
    # Validate inputs
    missing_by = [v for v in by_vars if v not in dataset.columns]
    if missing_by:
        raise ValueError(f"Column(s) {missing_by} not found in dataset (by_vars).")
    if source_var not in dataset.columns:
        raise ValueError(f"Column '{source_var}' not found in dataset (source_var).")

    # Identify baseline records
    if filter_add is None:
        baseline_mask = dataset.eval('ABLFL == "Y"')
    elif callable(filter_add):
        baseline_mask = filter_add(dataset)
    else:
        baseline_mask = dataset.eval(str(filter_add))

    baseline = dataset.loc[baseline_mask, by_vars + [source_var]].copy()

    # Ensure uniqueness per by_vars group
    dupes = baseline.duplicated(subset=by_vars, keep=False)
    if dupes.any():
        raise ValueError(
            f"Multiple baseline records found per by_vars group {by_vars}. "
            "Ensure at most one baseline record exists per group."
        )

    baseline = baseline.rename(columns={source_var: new_var})

    result = dataset.merge(baseline[by_vars + [new_var]], on=by_vars, how="left")
    return result


def derive_var_chg(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Derive change from baseline (``CHG``) in a BDS dataset.

    ``CHG`` is calculated as ``AVAL - BASE``.

    Mirrors ``derive_var_chg()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset. Must contain ``AVAL`` and ``BASE`` columns.

    Returns
    -------
    pd.DataFrame
        Input dataset with ``CHG`` appended.

    Raises
    ------
    ValueError
        If ``AVAL`` or ``BASE`` are missing from ``dataset``.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_var_chg
    >>> df = pd.DataFrame({
    ...     "USUBJID": ["P01", "P01"],
    ...     "PARAMCD": ["WEIGHT", "WEIGHT"],
    ...     "AVAL":    [80.0, 82.0],
    ...     "BASE":    [80.0, 80.0],
    ... })
    >>> derive_var_chg(df)
    """
    for col in ("AVAL", "BASE"):
        if col not in dataset.columns:
            raise ValueError(f"Column '{col}' not found in dataset.")

    result = dataset.copy()
    result["CHG"] = result["AVAL"] - result["BASE"]
    return result


def derive_var_pchg(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Derive percent change from baseline (``PCHG``) in a BDS dataset.

    ``PCHG`` is calculated as ``(AVAL - BASE) / abs(BASE) * 100``.  When
    ``BASE`` is zero the result is ``NaN`` (not a number).

    Mirrors ``derive_var_pchg()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset. Must contain ``AVAL`` and ``BASE`` columns.

    Returns
    -------
    pd.DataFrame
        Input dataset with ``PCHG`` appended.

    Raises
    ------
    ValueError
        If ``AVAL`` or ``BASE`` are missing from ``dataset``.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_var_pchg
    >>> df = pd.DataFrame({
    ...     "USUBJID": ["P01", "P01"],
    ...     "PARAMCD": ["WEIGHT", "WEIGHT"],
    ...     "AVAL":    [80.0, 82.0],
    ...     "BASE":    [80.0, 80.0],
    ... })
    >>> derive_var_pchg(df)
    """
    for col in ("AVAL", "BASE"):
        if col not in dataset.columns:
            raise ValueError(f"Column '{col}' not found in dataset.")

    result = dataset.copy()
    result["PCHG"] = np.where(
        result["BASE"] == 0,
        np.nan,
        (result["AVAL"] - result["BASE"]) / result["BASE"].abs() * 100,
    )
    return result
