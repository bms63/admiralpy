"""
admiralpy - Python implementation of the admiral R package.

A toolbox for creating ADaM (Analysis Data Model) datasets for
clinical trial data following CDISC standards, inspired by the
pharmaverse admiral R package.
"""

from admiralpy.derive_vars_dt import derive_vars_dt, derive_vars_dtm
from admiralpy.derive_var_baseline import (
    derive_var_base,
    derive_var_chg,
    derive_var_pchg,
)
from admiralpy.compute import compute_age_years, compute_bmi, compute_bsa
from admiralpy.derive_vars_merged import derive_vars_merged
from admiralpy.derive_param_computed import derive_param_computed
from admiralpy.convert_dtc import convert_dtc_to_dt, convert_dtc_to_dtm
from admiralpy.filter_extreme import filter_extreme

__all__ = [
    # Date/time derivations
    "derive_vars_dt",
    "derive_vars_dtm",
    # Baseline & change
    "derive_var_base",
    "derive_var_chg",
    "derive_var_pchg",
    # Compute utilities
    "compute_age_years",
    "compute_bmi",
    "compute_bsa",
    # Merge & computed parameters
    "derive_vars_merged",
    "derive_param_computed",
    # Conversion helpers
    "convert_dtc_to_dt",
    "convert_dtc_to_dtm",
    # Filter utilities
    "filter_extreme",
]

__version__ = "0.1.0"
