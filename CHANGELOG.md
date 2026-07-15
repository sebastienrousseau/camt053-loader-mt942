# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite (`camt053`, `camt053-mcp`, `camt053-lsp`, `camt053-writer-xlsx`,
`camt053-loader-mt940`); a `0.0.X` release of this package targets the
`0.0.X` release of `camt053`.

## [0.0.13] - 2026-07-16

### Added

- **Load/stress suite** (`tests/test_stress.py`) — `perf`-marked and
  excluded from the coverage-gated default run, mirroring the parent
  project's convention (select with `pytest -m perf --no-cov`):
  sustained concurrent conversions (32 threads × 20 iterations,
  zero-error and p95-latency gates), a 5,000-entry large-input
  wall-clock case, and a 500-iteration `tracemalloc` soak loop with a
  bounded memory-growth budget.

### Changed

- **Version** — suite-wide lockstep bump to `0.0.13`. No functional
  changes to the loader.

## [0.0.1] - 2026-07-12

### Added

First release of `camt053-loader-mt942`, a SWIFT MT942 → camt.052
`ParsedDocument` converter. Companion to the
[`camt053`](https://github.com/sebastienrousseau/camt053) core library.

Public API: a single function `parse_mt942(text)` that returns the
same `camt053.models.ParsedDocument` shape as
`camt053.parse.statement_parser.parse_document`, tagged as a
`camt.052.001.08` Bank-to-Customer Account Report, so every
downstream consumer in the suite works without further changes.

#### Supported MT942 fields

- `:20:` Transaction reference number
- `:25:` Account identification (BIC + account or account only)
- `:28C:` Statement / sequence number
- `:34F:` Floor limit indicator (debit / credit / unmarked)
- `:13D:` Date/time indication → report `creation_date_time`
- `:61:` Statement line (debit/credit, reversals via `RC`/`RD`,
  optional funds code, bank reference, customer reference)
- `:86:` Information to account owner (attaches to the preceding entry)
- `:90D:` / `:90C:` Number and sum of debit / credit entries

Floor limits and entry summaries are surfaced as proprietary
`type_code` balances (`FLIMD`/`FLIMC`, `SUMD:<n>`/`SUMC:<n>`) because
the camt.053-oriented typed model has no `<Lmt>` / `<TxsSummry>`
structures.
