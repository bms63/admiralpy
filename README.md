# admiralpy

A Python re-implementation of the [admiral](https://github.com/pharmaverse/admiral) R package — an open-source toolbox for creating **ADaM (Analysis Data Model)** datasets for clinical trials following [CDISC](https://www.cdisc.org/) standards.

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

| Function | Description |
|---|---|
| `derive_vars_dt()` | Derive a date variable (`*DT`) from a character DTC variable |
| `derive_vars_dtm()` | Derive a datetime variable (`*DTM`) from a character DTC variable |
| `derive_var_base()` | Derive a baseline variable (e.g. `BASE`) in a BDS dataset |
| `derive_var_chg()` | Derive change from baseline (`CHG = AVAL − BASE`) |
| `derive_var_pchg()` | Derive percent change from baseline (`PCHG`) |
| `compute_age_years()` | Convert age from any unit to years |
| `compute_bmi()` | Compute Body Mass Index (BMI) |
| `compute_bsa()` | Compute Body Surface Area (BSA) |

## Quick Start

```python
import pandas as pd
from admiralpy import (
    derive_vars_dt,
    derive_var_base,
    derive_var_chg,
    derive_var_pchg,
    compute_bmi,
)

# 1. Convert a DTC column to a date variable with day imputation
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
print(mhdt[["MHSTDTC", "ASTDT", "ASTDTF"]])

# 2. Derive BASE, CHG, and PCHG
advs = pd.DataFrame({
    "USUBJID": ["P01", "P01", "P01"],
    "PARAMCD": ["WEIGHT"] * 3,
    "AVAL":    [80.0, 80.8, 81.4],
    "ABLFL":   ["Y", None, None],
})
advs = derive_var_base(advs, by_vars=["USUBJID", "PARAMCD"])
advs = derive_var_chg(advs)
advs = derive_var_pchg(advs)
print(advs)

# 3. Compute BMI
bmi = compute_bmi(height=170, weight=75)
print(f"BMI: {bmi:.2f} kg/m²")
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Design Principles

`admiralpy` follows the same design philosophy as the R `admiral` package:

- **Usability** – thoroughly documented functions with clear examples.
- **Simplicity** – each function has a single, well-defined purpose.
- **Consistency** – naming conventions mirror the admiral R package (`derive_vars_*`, `derive_var_*`, `compute_*`).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
