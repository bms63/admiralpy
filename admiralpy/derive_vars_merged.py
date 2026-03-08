"""
Functions for merging variables from an additional dataset.

Mirrors ``derive_vars_merged()`` from the admiral R package.
"""

from typing import Callable, Dict, List, Optional, Union

import pandas as pd


def derive_vars_merged(
    dataset: pd.DataFrame,
    dataset_add: pd.DataFrame,
    by_vars: List[str],
    new_vars: Optional[Dict[str, str]] = None,
    filter_add: Optional[Union[str, Callable]] = None,
    order: Optional[List[str]] = None,
    mode: Optional[str] = None,
    relationship: str = "many-to-one",
) -> pd.DataFrame:
    """
    Add variable(s) from an additional dataset to the input dataset.

    For each observation in ``dataset``, the matching record(s) in
    ``dataset_add`` are identified using ``by_vars``.  If ``order`` and
    ``mode`` are specified, only the first or last matching record is used.
    The variables listed in ``new_vars`` are then merged into ``dataset``.

    Mirrors ``derive_vars_merged()`` from the admiral R package.

    Parameters
    ----------
    dataset : pd.DataFrame
        Input dataset.
    dataset_add : pd.DataFrame
        Additional dataset providing the new variables.  Must contain all
        columns listed in ``by_vars``.
    by_vars : list of str
        Variables used to match observations across the two datasets.
    new_vars : dict, optional
        Mapping of ``{new_column_name: source_column_name}``.  When
        ``source_column_name`` is the same as ``new_column_name`` you can
        simply list the column name as both key and value.

        If ``None``, all columns in ``dataset_add`` that are *not* in
        ``by_vars`` and not already in ``dataset`` are added.
    filter_add : str or callable, optional
        Condition applied to ``dataset_add`` before the merge.

        * **string** – passed to :meth:`pandas.DataFrame.query`.
        * **callable** – receives ``dataset_add`` and returns a boolean Series.
    order : list of str, optional
        Column names used to sort ``dataset_add`` within each ``by_vars``
        group before selecting the first/last record.  Prefix a column name
        with ``"-"`` for descending sort (e.g. ``["-EXSTDTM", "EXSEQ"]``).
    mode : {"first", "last"}, optional
        When ``order`` is supplied, selects the ``"first"`` or ``"last"``
        record per ``by_vars`` group.  Must be provided together with
        ``order``.
    relationship : str, optional
        Merge cardinality.  Kept for API compatibility.  Default is
        ``"many-to-one"``.

    Returns
    -------
    pd.DataFrame
        Input dataset with the new variable(s) appended.

    Raises
    ------
    ValueError
        If ``by_vars`` are missing from either dataset, if ``new_vars``
        source columns are missing from ``dataset_add``, or if ``mode`` is
        provided without ``order`` (or vice-versa).

    Examples
    --------
    >>> import pandas as pd
    >>> from admiralpy import derive_vars_merged
    >>> adsl = pd.DataFrame({"USUBJID": ["P01", "P02"], "AGE": [30, 40]})
    >>> ex = pd.DataFrame({
    ...     "USUBJID":  ["P01", "P01", "P02"],
    ...     "EXSTDTC":  ["2020-01-01", "2020-02-01", "2020-01-15"],
    ...     "EXSEQ":    [1, 2, 1],
    ... })
    >>> derive_vars_merged(
    ...     adsl, ex,
    ...     by_vars=["USUBJID"],
    ...     new_vars={"TRTSTDTC": "EXSTDTC"},
    ...     order=["EXSEQ"],
    ...     mode="first",
    ... )
    """
    # ---- validate by_vars ------------------------------------------------
    for col in by_vars:
        if col not in dataset.columns:
            raise ValueError(f"Column '{col}' not found in dataset (by_vars).")
        if col not in dataset_add.columns:
            raise ValueError(
                f"Column '{col}' not found in dataset_add (by_vars)."
            )

    # ---- validate mode / order pair --------------------------------------
    if (order is None) != (mode is None):
        raise ValueError(
            "Both 'order' and 'mode' must be specified together, or both omitted."
        )
    if mode is not None and mode not in ("first", "last"):
        raise ValueError(f"mode must be 'first' or 'last', got '{mode}'.")

    # ---- apply filter_add ------------------------------------------------
    if filter_add is None:
        add = dataset_add.copy()
    elif callable(filter_add):
        add = dataset_add.loc[filter_add(dataset_add)].copy()
    else:
        add = dataset_add.query(str(filter_add)).copy()

    # ---- sort + select first/last ----------------------------------------
    if order is not None:
        # Parse column names: prefix "-" means descending
        sort_cols = []
        ascending = []
        for col in order:
            if col.startswith("-"):
                sort_cols.append(col[1:])
                ascending.append(False)
            else:
                sort_cols.append(col)
                ascending.append(True)

        add = add.sort_values(sort_cols, ascending=ascending)
        if mode == "first":
            add = add.groupby(by_vars, sort=False).first().reset_index()
        else:
            add = add.groupby(by_vars, sort=False).last().reset_index()

    # ---- resolve new_vars ------------------------------------------------
    if new_vars is None:
        # Add all columns from dataset_add not already in dataset
        extra_cols = [
            c for c in add.columns if c not in by_vars and c not in dataset.columns
        ]
        add_subset = add[by_vars + extra_cols]
    else:
        # Validate source columns exist
        for new_name, src_name in new_vars.items():
            if src_name not in add.columns:
                raise ValueError(
                    f"Source column '{src_name}' not found in dataset_add."
                )
        add_subset = add[by_vars + list(set(new_vars.values()))].copy()
        # Rename if new name differs from source name
        rename_map = {v: k for k, v in new_vars.items() if k != v}
        if rename_map:
            add_subset = add_subset.rename(columns=rename_map)
        # Keep only by_vars + new column names
        add_subset = add_subset[by_vars + list(new_vars.keys())]

    result = dataset.merge(add_subset, on=by_vars, how="left")
    return result
