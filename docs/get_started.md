# Get Started

## Main Idea

The main idea of `admiralpy` is that an **ADaM dataset is built by a sequence of
derivations**.  Each derivation adds one or more variables or records to the
processed dataset.  This modular approach makes it easy to adjust code by adding,
removing, or modifying individual derivation steps.  Each derivation is a single
function call that accepts a `pandas.DataFrame` and returns a new `DataFrame`.

In this guide we explore the different types of derivation functions offered by
`admiralpy`, the naming conventions they follow, and how to chain them together.

---

## Setup

We will use a small set of illustrative SDTM-like datasets throughout this guide.
In a real project you would read these from SAS Transport (XPT) files or a data
warehouse.

```python
import pandas as pd
import numpy as np
from admiralpy import (
    derive_vars_dtm,
    derive_vars_merged,
    derive_param_computed,
    convert_dtc_to_dt,
    filter_extreme,
    derive_var_base,
    derive_var_chg,
    derive_var_pchg,
)

# ── Exposure (EX) ─────────────────────────────────────────────────────────────
ex = pd.DataFrame({
    "STUDYID": ["PILOT01"] * 5,
    "USUBJID": ["01-701-1015", "01-701-1015", "01-701-1023",
                "01-703-1086", "01-716-1024"],
    "EXSEQ":   [1, 2, 1, 1, 1],
    "EXSTDTC": [
        "2014-01-02T10:00",
        "2014-02-01T08:00",
        "2014-01-05T09:30",
        "2014-01-08T11:00",
        "2014-01-10T14:00",
    ],
    "EXTRT":   ["XANO", "XANO", "XANO", "XANO", "XANO"],
    "EXDOSE":  [54, 54, 54, 54, 54],
})

# ── Demographics (DM) ─────────────────────────────────────────────────────────
dm = pd.DataFrame({
    "STUDYID": ["PILOT01"] * 5,
    "USUBJID": ["01-701-1015", "01-701-1023", "01-703-1086",
                "01-703-1096", "01-716-1024"],
    "RFSTDTC": [
        "2014-01-02",
        "2014-01-05",
        "2014-01-08",
        "2014-01-12",
        "2014-01-10",
    ],
    "AGE":     [63, 52, 70, 45, 58],
    "SEX":     ["F", "M", "F", "M", "F"],
    "COUNTRY": ["USA", "USA", "CAN", "CAN", "USA"],
})

# ── Disposition (DS) ─────────────────────────────────────────────────────────
ds = pd.DataFrame({
    "STUDYID": ["PILOT01"] * 5,
    "USUBJID": ["01-701-1015", "01-701-1023", "01-703-1086",
                "01-703-1096", "01-716-1024"],
    "DSDECOD": ["FINAL LAB VISIT", "FINAL LAB VISIT", "COMPLETED",
                "FINAL LAB VISIT", "COMPLETED"],
    "DSSTDTC": [
        "2014-07-02",
        "2014-07-10",
        "2014-06-20",
        "2014-07-15",
        "2014-06-28",
    ],
})

# ── Vital Signs (VS) ──────────────────────────────────────────────────────────
vs = pd.DataFrame({
    "USUBJID": (["01-701-1015"] * 4 + ["01-701-1023"] * 4),
    "VSTESTCD": ["SYSBP", "DIABP", "SYSBP", "DIABP"] * 2,
    "VSSTRESN": [121.0, 51.0, 121.0, 50.0, 130.0, 79.0, 128.0, 77.0],
    "VSPOS":    ["SUPINE"] * 8,
    "VISIT":    ["Baseline", "Baseline", "Week 2", "Week 2"] * 2,
    "VISITNUM": [1, 1, 3, 3] * 2,
})

# Build a working ADVS base
advs = vs.assign(
    PARAM    = vs["VSTESTCD"].map({"SYSBP": "Systolic BP (mmHg)",
                                   "DIABP": "Diastolic BP (mmHg)"}),
    PARAMCD  = vs["VSTESTCD"],
    AVAL     = vs["VSSTRESN"],
    AVISIT   = vs["VISIT"],
    AVISITN  = vs["VISITNUM"],
)

# Build an ADSL skeleton
adsl = dm.copy()

print("EX shape:", ex.shape)
print("DM shape:", dm.shape)
print("ADVS shape:", advs.shape)
```

```
EX shape: (5, 7)
DM shape: (5, 6)
ADVS shape: (8, 9)
```

---

## Derivation Functions

The most important functions in `admiralpy` are the **derivation functions**.
They add variables or records to the input dataset without changing existing
rows.  All derivation functions start with `derive_`.

| Prefix | Pattern | Example |
|---|---|---|
| `derive_var_*` | Derives a single variable | `derive_var_base()` → `BASE` |
| `derive_vars_*` | Can derive multiple variables | `derive_vars_dt()` → `*DT` + `*DTF` |
| `derive_param_*` | Derives a new parameter record | `derive_param_computed()` → MAP |

### Example: Adding Variables with `derive_vars_merged`

`derive_vars_merged()` adds variable(s) from an additional dataset, mirroring
the R `derive_vars_merged()` function.

Below we add the **treatment start datetime** (`TRTSDTM`) and its imputation
flag (`TRTSTMF`) to `adsl` by pulling the first non-missing exposure start
datetime for each subject.

```python
# Step 1: Convert the DTC string to a proper datetime column
ex_ext = derive_vars_dtm(
    ex,
    dtc="EXSTDTC",
    new_vars_prefix="EXST",
    highest_imputation="n",
)

print(ex_ext[["USUBJID", "EXSTDTM"]].head())
```

```
      USUBJID              EXSTDTM
0  01-701-1015  2014-01-02 10:00:00
1  01-701-1015  2014-02-01 08:00:00
2  01-701-1023  2014-01-05 09:30:00
3  01-703-1086  2014-01-08 11:00:00
4  01-716-1024  2014-01-10 14:00:00
```

```python
# Step 2: Merge TRTSDTM (first exposure datetime per subject) into ADSL
adsl = derive_vars_merged(
    adsl,
    dataset_add=ex_ext,
    by_vars=["STUDYID", "USUBJID"],
    new_vars={"TRTSDTM": "EXSTDTM", "TRTSTMF": "EXSTTMF"},
    filter_add=lambda df: df["EXSTDTM"].notna(),
    order=["EXSTDTM", "EXSEQ"],
    mode="first",
)

print(adsl[["USUBJID", "TRTSDTM", "TRTSTMF"]])
```

```
       USUBJID             TRTSDTM TRTSTMF
0  01-701-1015 2014-01-02 10:00:00    None
1  01-701-1023 2014-01-05 09:30:00    None
2  01-703-1086 2014-01-08 11:00:00    None
3  01-703-1096             NaT      None
4  01-716-1024 2014-01-10 14:00:00    None
```

### Example: Adding Records with `derive_param_computed`

`derive_param_computed()` adds a **derived parameter record** for each
by-group.  Below we compute Mean Arterial Pressure (MAP) from SYSBP and DIABP:

$$MAP = \frac{SYSBP + 2 \times DIABP}{3}$$

```python
advs = derive_param_computed(
    advs,
    by_vars=["USUBJID", "AVISIT", "AVISITN"],
    parameters=["SYSBP", "DIABP"],
    set_values_to={
        "AVAL":    lambda w: (w["AVAL_SYSBP"] + 2 * w["AVAL_DIABP"]) / 3,
        "PARAMCD": "MAP",
        "PARAM":   "Mean Arterial Pressure (mmHg)",
    },
)

print(
    advs[advs["PARAMCD"] == "MAP"][
        ["USUBJID", "AVISIT", "PARAMCD", "AVAL"]
    ].reset_index(drop=True)
)
```

```
      USUBJID    AVISIT PARAMCD       AVAL
0  01-701-1015  Baseline     MAP  74.333333
1  01-701-1015    Week 2     MAP  73.666667
2  01-701-1023  Baseline     MAP  96.000000
3  01-701-1023    Week 2     MAP  94.000000
```

!!! note
    For convenience, `admiralpy` also provides `compute_bmi()` and
    `compute_bsa()` to directly compute BMI and BSA parameters.

---

## Other Types of Functions

### Computation Functions

**Computation functions** operate on scalar values or `pd.Series` objects and
return converted values.  They are typically used inside
`DataFrame.assign()` / `mutate()` calls.

```python
# Add the date of the final lab visit to ADSL using convert_dtc_to_dt()
adsl_labs = derive_vars_merged(
    dm,
    dataset_add=ds,
    by_vars=["USUBJID"],
    new_vars={"FINLABDT": "DSSTDTC"},
    filter_add='DSDECOD == "FINAL LAB VISIT"',
)

adsl_labs["FINLABDT"] = convert_dtc_to_dt(adsl_labs["FINLABDT"])

print(adsl_labs[["USUBJID", "FINLABDT"]])
```

```
       USUBJID    FINLABDT
0  01-701-1015  2014-07-02
1  01-701-1023  2014-07-10
2  01-703-1086         NaT
3  01-703-1096  2014-07-15
4  01-716-1024         NaT
```

`convert_dtc_to_dt()` can also be applied in a `DataFrame.assign()` call:

```python
adsl_labs = adsl_labs.assign(
    RFSTDT=lambda df: convert_dtc_to_dt(df["RFSTDTC"])
)
print(adsl_labs[["USUBJID", "RFSTDTC", "RFSTDT"]].head(3))
```

```
       USUBJID    RFSTDTC     RFSTDT
0  01-701-1015  2014-01-02 2014-01-02
1  01-701-1023  2014-01-05 2014-01-05
2  01-703-1086  2014-01-08 2014-01-08
```

### Filter Functions

**Filter functions** return a subset of the input dataset.  `filter_extreme()`
extracts the first or last record within each by-group.

```python
# Extract the most recent MAP record per subject
advs_lastmap = (
    advs[advs["PARAMCD"] == "MAP"]
    .pipe(
        filter_extreme,
        by_vars=["USUBJID"],
        order=["AVISITN", "PARAMCD"],
        mode="last",
    )
)

print(advs_lastmap[["USUBJID", "AVISIT", "PARAMCD", "AVAL"]].reset_index(drop=True))
```

```
      USUBJID  AVISIT PARAMCD       AVAL
0  01-701-1015  Week 2     MAP  73.666667
1  01-701-1023  Week 2     MAP  94.000000
```

---

## BDS Findings Workflow: Baseline, CHG, and PCHG

A very common BDS workflow derives baseline (`BASE`), change from baseline
(`CHG`), and percent change from baseline (`PCHG`).

```python
# Add a baseline flag column for the first visit
advs_bds = advs.copy()
advs_bds["ABLFL"] = advs_bds["AVISITN"].apply(lambda x: "Y" if x == 1 else None)

# Chain all three derivations together
advs_bds = (
    advs_bds
    .pipe(derive_var_base, by_vars=["USUBJID", "PARAMCD"])
    .pipe(derive_var_chg)
    .pipe(derive_var_pchg)
)

print(
    advs_bds[["USUBJID", "PARAMCD", "AVISIT", "AVAL", "BASE", "CHG", "PCHG"]]
    .sort_values(["USUBJID", "PARAMCD", "AVISITN"])
    .reset_index(drop=True)
)
```

```
       USUBJID PARAMCD    AVISIT   AVAL   BASE   CHG       PCHG
0  01-701-1015   DIABP  Baseline   51.0   51.0   0.0   0.000000
1  01-701-1015   DIABP    Week 2   50.0   51.0  -1.0  -1.960784
2  01-701-1015     MAP  Baseline  74.33  74.33   0.0   0.000000
...
```

---

## Date/Time Derivation

`derive_vars_dt()` converts an ISO 8601 character DTC column to a proper
date variable, with optional partial-date imputation.

```python
from admiralpy import derive_vars_dt

mhdt = pd.DataFrame({
    "MHSTDTC": [
        "2019-07-18T15:25:40",   # full datetime → date extracted
        "2019-07-18",            # complete date
        "2019-02",               # missing day  → imputed to first
        "2019",                  # missing month+day → imputed to Jan 1
        "",                      # empty → NaT
    ]
})

result = derive_vars_dt(
    mhdt,
    new_vars_prefix="AST",
    dtc="MHSTDTC",
    highest_imputation="M",   # impute up to month level
    date_imputation="first",
)

print(result)
```

```
              MHSTDTC      ASTDT ASTDTF
0  2019-07-18T15:25:40 2019-07-18   None
1          2019-07-18  2019-07-18   None
2             2019-02  2019-02-01      D
3                2019  2019-01-01      M
4                       NaT       None
```

The `ASTDTF` flag column indicates which date component was imputed:
`"D"` = day, `"M"` = month (and day).

---

## Naming Conventions

`admiralpy` uses consistent naming to make functions easy to find:

| Pattern | Description |
|---|---|
| `derive_var_*` | Derives a **single** variable |
| `derive_vars_*` | Can derive **multiple** variables |
| `derive_param_*` | Derives a **new parameter record** |
| `compute_*` | Vector computation (scalar or Series input) |
| `convert_*` | Type conversion helper |
| `filter_*` | Returns a **filtered subset** of the input dataset |

---

## Next Steps

- Explore the full [API Reference](api/derive_vars_dt.md) for detailed parameter
  descriptions and more examples.
- See the [Changelog](changelog.md) for the list of functions available in the
  current release.
- Raise issues or ask questions on the
  [GitHub repository](https://github.com/bms63/admiralpy/issues).
