"""
Filter utility functions for ADaM dataset manipulation.

These functions mirror ``filter_extreme()`` from the admiral R package.
"""

from typing import List, Optional, Union

import pandas as pd


def filter_extreme(
    dataset: pd.DataFrame,
    order: List[str],
    mode: str,
    by_vars: Optional[List[str]] = None,
    check_type: str = "warning",
) -> pd.DataFrame:
    """
    Filter the first or last observation (per by group) from a dataset.

    For each group defined by ``by_vars``, the observations are sorted by
    ``order`` and the first or last record is retained.  If ``by_vars`` is
    ``None``, the entire dataset is treated as a single group.

    Mirrors ``filter_extreme()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset.
    order : list of str
        Column names used for sorting within each group.  Prefix a column
        name with ``"-"`` for descending sort (e.g. ``["-AVISITN", "PARAMCD"]``).
    mode : {"first", "last"}
        Whether to retain the ``"first"`` or ``"last"`` observation after sorting.
    by_vars : list of str, optional
        Grouping variables.  If ``None``, the whole dataset is treated as one
        group.
    check_type : {"none", "warning", "error"}, optional
        Uniqueness check.  If ``"warning"`` or ``"error"``, a diagnostic is
        raised when duplicate (by ``by_vars`` + ``order``) records are found.
        Default is ``"warning"``.

    Returns
    -------
    pd.DataFrame
        Dataset containing only the selected (first or last) records.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"first"`` or ``"last"``.
    ValueError
        If any column in ``by_vars`` or ``order`` is missing from ``dataset``.
    RuntimeError
        If ``check_type="error"`` and duplicate records are found.

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import filter_extreme
    >>> advs = pd.DataFrame({
    ...     "USUBJID": ["P01", "P01", "P01"],
    ...     "PARAMCD": ["MAP", "MAP", "MAP"],
    ...     "AVISITN": [0, 2, 4],
    ...     "AVAL":    [93.0, 91.5, 94.0],
    ... })
    >>> filter_extreme(
    ...     advs,
    ...     by_vars=["USUBJID"],
    ...     order=["AVISITN", "PARAMCD"],
    ...     mode="last",
    ... )
    """
    mode = mode.lower()
    if mode not in ("first", "last"):
        raise ValueError(f"mode must be 'first' or 'last', got '{mode}'.")

    # Validate columns
    if by_vars:
        for col in by_vars:
            if col not in dataset.columns:
                raise ValueError(
                    f"Column '{col}' not found in dataset (by_vars)."
                )

    # Parse sort order
    sort_cols = []
    ascending = []
    for col in order:
        if col.startswith("-"):
            sort_cols.append(col[1:])
            ascending.append(False)
        else:
            sort_cols.append(col)
            ascending.append(True)

    for col in sort_cols:
        if col not in dataset.columns:
            raise ValueError(f"Column '{col}' not found in dataset (order).")

    # ---- uniqueness check ------------------------------------------------
    if check_type in ("warning", "error") and by_vars:
        check_cols = (by_vars or []) + sort_cols
        check_cols = [c for c in check_cols if c in dataset.columns]
        if dataset.duplicated(subset=check_cols).any():
            msg = (
                f"Duplicate records found with respect to {check_cols}. "
                "The selected record may not be unique."
            )
            if check_type == "error":
                raise RuntimeError(msg)
            import warnings
            warnings.warn(msg, stacklevel=2)

    # ---- sort and select -------------------------------------------------
    sorted_df = dataset.sort_values(sort_cols, ascending=ascending)

    if by_vars:
        if mode == "first":
            result = sorted_df.groupby(by_vars, sort=False).first().reset_index()
        else:
            result = sorted_df.groupby(by_vars, sort=False).last().reset_index()
    else:
        result = sorted_df.iloc[[0]] if mode == "first" else sorted_df.iloc[[-1]]
        result = result.reset_index(drop=True)

    # Restore original column order
    result = result[[c for c in dataset.columns if c in result.columns]]
    return result
