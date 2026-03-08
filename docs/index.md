# admiralpy

**admiralpy** is a Python implementation of the [admiral](https://github.com/pharmaverse/admiral)
R package — an open-source toolbox for creating **ADaM (Analysis Data Model)** datasets
for clinical trials following [CDISC](https://www.cdisc.org/) standards.

!!! tip "New to admiralpy?"
    Start with the [Get Started](get_started.md) guide to see working examples
    of the most common derivation workflows.

## Installation

```bash
pip install admiralpy
```

Or install directly from the GitHub repository:

```bash
pip install git+https://github.com/bms63/admiralpy.git
```

## Available Functions

| Category | Function | Description |
|---|---|---|
| **Date/Time** | `derive_vars_dt()` | Derive a date variable (`*DT`) from a DTC character variable |
| | `derive_vars_dtm()` | Derive a datetime variable (`*DTM`) from a DTC character variable |
| **Baseline** | `derive_var_base()` | Derive a baseline variable (e.g. `BASE`) |
| | `derive_var_chg()` | Derive change from baseline (`CHG`) |
| | `derive_var_pchg()` | Derive percent change from baseline (`PCHG`) |
| **Merge** | `derive_vars_merged()` | Add variables from an additional dataset |
| **Parameters** | `derive_param_computed()` | Add a derived parameter record (e.g. MAP) |
| **Filter** | `filter_extreme()` | Filter first/last record per by-group |
| **Convert** | `convert_dtc_to_dt()` | Convert DTC string to a date |
| | `convert_dtc_to_dtm()` | Convert DTC string to a datetime |
| **Compute** | `compute_age_years()` | Convert age to years |
| | `compute_bmi()` | Body Mass Index |
| | `compute_bsa()` | Body Surface Area (4 formulae) |

## Design Principles

`admiralpy` follows the same design philosophy as the R `admiral` package:

- **Usability** — thoroughly documented functions with clear examples.
- **Simplicity** — each function has a single, well-defined purpose.
- **Findability** — consistent naming: `derive_vars_*`, `derive_var_*`,
  `derive_param_*`, `compute_*`, `convert_*`, `filter_*`.
- **Readability** — chain derivations together with standard Python pandas
  method chaining.

## Quick Example

```python
import pandas as pd
from admiralpy import (
    derive_vars_dt,
    derive_var_base,
    derive_var_chg,
    derive_var_pchg,
    compute_bmi,
)

# Convert DTC columns to date variables
mhdt = pd.DataFrame({
    "MHSTDTC": ["2019-07-18T15:25:40", "2019-07-18", "2019-02", "2019", ""]
})
mhdt = derive_vars_dt(
    mhdt,
    new_vars_prefix="AST",
    dtc="MHSTDTC",
    highest_imputation="M",
    date_imputation="first",
)

# Derive baseline, change and percent change
advs = pd.DataFrame({
    "USUBJID": ["P01", "P01", "P01"],
    "PARAMCD": ["WEIGHT"] * 3,
    "AVAL":    [80.0, 80.8, 81.4],
    "ABLFL":   ["Y", None, None],
})
advs = (advs
    .pipe(derive_var_base, by_vars=["USUBJID", "PARAMCD"])
    .pipe(derive_var_chg)
    .pipe(derive_var_pchg)
)
```
