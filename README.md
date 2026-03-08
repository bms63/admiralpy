# admiralpy

A Python re-implementation of the [admiral](https://github.com/pharmaverse/admiral) R package — an open-source toolbox for creating **ADaM (Analysis Data Model)** datasets for clinical trials following [CDISC](https://www.cdisc.org/) standards.

📖 **[Full documentation & Get Started guide](https://bms63.github.io/admiralpy/)**

## Installation

```bash
pip install admiralpy
```

Or install directly from source:

```bash
git clone https://github.com/bms63/admiralpy.git
cd admiralpy
pip install -e ".[dev]"
```

## Features

| Category | Function | Description |
|---|---|---|
| Date/Time | `derive_vars_dt()` | Derive a date variable (`*DT`) from a DTC character variable |
| | `derive_vars_dtm()` | Derive a datetime variable (`*DTM`) from a DTC character variable |
| Baseline | `derive_var_base()` | Derive a baseline variable (e.g. `BASE`) in a BDS dataset |
| | `derive_var_chg()` | Derive change from baseline (`CHG = AVAL − BASE`) |
| | `derive_var_pchg()` | Derive percent change from baseline (`PCHG`) |
| Merge | `derive_vars_merged()` | Add variables from an additional dataset |
| Parameters | `derive_param_computed()` | Add a derived parameter record (e.g. MAP) |
| Filter | `filter_extreme()` | Filter first/last record per by-group |
| Convert | `convert_dtc_to_dt()` | Convert DTC string to a date |
| | `convert_dtc_to_dtm()` | Convert DTC string to a datetime |
| Compute | `compute_age_years()` | Convert age from any unit to years |
| | `compute_bmi()` | Body Mass Index |
| | `compute_bsa()` | Body Surface Area (4 formulae) |

## Quick Start

```python
import pandas as pd
from admiralpy import (
    derive_vars_dt,
    derive_vars_merged,
    derive_param_computed,
    derive_var_base,
    derive_var_chg,
    derive_var_pchg,
    filter_extreme,
    convert_dtc_to_dt,
)

# 1. Convert DTC to date with partial-date imputation
mhdt = pd.DataFrame({
    "MHSTDTC": ["2019-07-18T15:25:40", "2019-07-18", "2019-02", "2019", ""]
})
mhdt = derive_vars_dt(mhdt, new_vars_prefix="AST", dtc="MHSTDTC",
                       highest_imputation="M", date_imputation="first")

# 2. Compute derived parameters (MAP from SYSBP + DIABP)
advs = pd.DataFrame({
    "USUBJID": ["P01"]*4, "AVISIT": ["BL"]*2 + ["W2"]*2,
    "AVISITN": [0]*2 + [2]*2,
    "PARAMCD": ["SYSBP", "DIABP"]*2, "AVAL": [120.0, 80.0, 118.0, 78.0],
})
advs = derive_param_computed(
    advs, by_vars=["USUBJID", "AVISIT", "AVISITN"],
    parameters=["SYSBP", "DIABP"],
    set_values_to={
        "AVAL": lambda w: (w["AVAL_SYSBP"] + 2 * w["AVAL_DIABP"]) / 3,
        "PARAMCD": "MAP", "PARAM": "Mean Arterial Pressure (mmHg)",
    },
)

# 3. Filter to last visit per subject
last_map = filter_extreme(
    advs[advs["PARAMCD"] == "MAP"],
    by_vars=["USUBJID"], order=["AVISITN"], mode="last",
)
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Building the Documentation Locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Design Principles

`admiralpy` follows the same design philosophy as the R `admiral` package:

- **Usability** – thoroughly documented functions with clear examples.
- **Simplicity** – each function has a single, well-defined purpose.
- **Consistency** – naming conventions mirror admiral (`derive_vars_*`, `derive_var_*`, `compute_*`).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
