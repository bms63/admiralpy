# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-08

### Added

- `derive_vars_dt()` – Derive a date variable (`*DT`) and optional date
  imputation flag (`*DTF`) from a character DTC variable.  Supports
  partial-date imputation to first, last, mid, or a specific `MM-DD` value
  up to year, month, or day level (`highest_imputation`).

- `derive_vars_dtm()` – Derive a datetime variable (`*DTM`) and optional
  imputation flag (`*DTMF`) from a character DTC variable.  Supports date
  imputation (same as `derive_vars_dt`) and time imputation to first
  (`00:00:00`) or last (`23:59:59`).

- `derive_var_base()` – Derive a baseline variable (e.g. `BASE`) in a BDS
  dataset by merging the baseline record (default: `ABLFL == "Y"`) back to
  all records within each `by_vars` group.

- `derive_var_chg()` – Derive change from baseline (`CHG = AVAL − BASE`).

- `derive_var_pchg()` – Derive percent change from baseline
  (`PCHG = (AVAL − BASE) / |BASE| × 100`; `NaN` when `BASE == 0`).

- `compute_age_years()` – Convert age values from any supported time unit
  (years, months, weeks, days, hours, minutes, seconds) to years, using
  365.25 days per year.

- `compute_bmi()` – Compute Body Mass Index (`BMI = weight / (height/100)²`;
  height in cm, weight in kg).

- `compute_bsa()` – Compute Body Surface Area using one of four formulae:
  Mosteller (default), DuBois, Haycock, or Gehan-George.

- Full test suite covering all public functions.

- `pyproject.toml` packaging configuration for publication to PyPI.
