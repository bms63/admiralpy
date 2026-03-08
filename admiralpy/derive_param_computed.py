"""
Functions for adding derived parameter records to a BDS dataset.

Mirrors ``derive_param_computed()`` from the admiral R package.
"""

from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd


def derive_param_computed(
    dataset: pd.DataFrame,
    by_vars: List[str],
    parameters: List[str],
    set_values_to: Dict[str, Union[str, Callable]],
    filter_add: Optional[Union[str, Callable]] = None,
    keep_nas: bool = False,
) -> pd.DataFrame:
    """
    Add a parameter computed from the analysis values of other parameters.

    For each group defined by ``by_vars``, a new record is created that
    contains the derived parameter.  The analysis values of other parameters
    are made available under the name ``<variable>_<PARAMCD>``
    (e.g. ``AVAL_SYSBP``).

    Mirrors ``derive_param_computed()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input BDS dataset.  Must contain ``PARAMCD`` and all columns listed
        in ``by_vars``.
    by_vars : list of str
        Variables that uniquely identify the group for which the new record
        is created (e.g. ``["USUBJID", "AVISIT", "AVISITN"]``).
    parameters : list of str
        ``PARAMCD`` values required for the computation.  The dataset must
        contain exactly one record per ``by_vars`` group for each parameter
        code.
    set_values_to : dict
        Mapping of ``{column_name: value_or_expression}``.

        * **scalar / string** – assigned as a constant to the new column.
        * **callable** – receives the *wide* DataFrame (one row per
          ``by_vars`` group, with columns named ``<col>_<PARAMCD>``) and
          must return a Series of the same length.

        Example::

            set_values_to={
                "AVAL": lambda w: (w["AVAL_SYSBP"] + 2 * w["AVAL_DIABP"]) / 3,
                "PARAMCD": "MAP",
                "PARAM": "Mean Arterial Pressure (mmHg)",
            }

    filter_add : str or callable, optional
        Condition applied to ``dataset`` before the computation.  Only the
        filtered records are used to derive the new parameter.
    keep_nas : bool, optional
        If ``True``, a new record is added even when some contributing values
        are ``NaN``.  Default is ``False`` (groups with any ``NaN``
        contributing value are skipped).

    Returns
    -------
    pd.DataFrame
        Input dataset with the new parameter record appended.  Variables not
        specified in ``by_vars`` or ``set_values_to`` are set to ``NaN`` in
        the new rows.

    Raises
    ------
    ValueError
        If ``PARAMCD`` is not present in ``dataset``, or if any column in
        ``by_vars`` is missing.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_param_computed
    >>> advs = pd.DataFrame({
    ...     "USUBJID":  ["P01", "P01", "P01", "P01"],
    ...     "AVISIT":   ["BASELINE", "BASELINE", "WEEK 2", "WEEK 2"],
    ...     "PARAMCD":  ["SYSBP", "DIABP", "SYSBP", "DIABP"],
    ...     "AVAL":     [120.0, 80.0, 118.0, 78.0],
    ... })
    >>> derive_param_computed(
    ...     advs,
    ...     by_vars=["USUBJID", "AVISIT"],
    ...     parameters=["SYSBP", "DIABP"],
    ...     set_values_to={
    ...         "AVAL": lambda w: (w["AVAL_SYSBP"] + 2 * w["AVAL_DIABP"]) / 3,
    ...         "PARAMCD": "MAP",
    ...         "PARAM": "Mean Arterial Pressure (mmHg)",
    ...     },
    ... )
    """
    if "PARAMCD" not in dataset.columns:
        raise ValueError("Column 'PARAMCD' not found in dataset.")
    for col in by_vars:
        if col not in dataset.columns:
            raise ValueError(f"Column '{col}' not found in dataset (by_vars).")

    # ---- filter ----------------------------------------------------------
    if filter_add is None:
        working = dataset
    elif callable(filter_add):
        working = dataset.loc[filter_add(dataset)]
    else:
        working = dataset.query(str(filter_add))

    # ---- pivot parameters to wide format ---------------------------------
    # Keep only the records for the requested parameters
    param_data = working[working["PARAMCD"].isin(parameters)]

    # Determine which columns to pivot (all columns except by_vars and PARAMCD)
    value_cols = [c for c in dataset.columns if c not in by_vars + ["PARAMCD"]]

    # Pivot: columns become <value_col>_<PARAMCD>
    wide = param_data.pivot_table(
        index=by_vars,
        columns="PARAMCD",
        values=value_cols,
        aggfunc="first",
        dropna=False,
    )

    # Flatten MultiIndex columns: (col, PARAMCD) → col_PARAMCD
    wide.columns = [f"{col}_{paramcd}" for col, paramcd in wide.columns]
    wide = wide.reset_index()

    # Ensure all expected parameter columns exist (fill missing with NaN)
    for p in parameters:
        for vc in value_cols:
            expected_col = f"{vc}_{p}"
            if expected_col not in wide.columns:
                wide[expected_col] = np.nan

    # ---- optionally drop groups with NaN contributing values -------------
    if not keep_nas:
        aval_cols = [f"AVAL_{p}" for p in parameters if f"AVAL_{p}" in wide.columns]
        if aval_cols:
            wide = wide.dropna(subset=aval_cols)

    if wide.empty:
        return dataset.copy()

    # ---- build new rows --------------------------------------------------
    new_rows = wide[by_vars].copy()

    for col_name, value in set_values_to.items():
        if callable(value):
            new_rows[col_name] = value(wide).values
        else:
            new_rows[col_name] = value

    # ---- align columns to input dataset ----------------------------------
    for col in dataset.columns:
        if col not in new_rows.columns:
            new_rows[col] = np.nan

    new_rows = new_rows[dataset.columns]

    result = pd.concat([dataset, new_rows], ignore_index=True)
    return result
