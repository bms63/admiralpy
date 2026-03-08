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

__all__ = [
    "derive_vars_dt",
    "derive_vars_dtm",
    "derive_var_base",
    "derive_var_chg",
    "derive_var_pchg",
    "compute_age_years",
    "compute_bmi",
    "compute_bsa",
]

__version__ = "0.1.0"
