<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`camt053`](https://github.com/sebastienrousseau/camt053)
suite (`camt053`, `camt053-mcp`, `camt053-lsp`, `camt053-writer-xlsx`,
`camt053-loader-mt940`); a `0.0.X` release of this package targets the
`0.0.X` release of `camt053`.

## [Unreleased]

### Removed

- **Python 3.10 is no longer supported; the floor is 3.11.** This is a
  decision for the whole camt053 suite: 3.10 reaches end of life in
  October 2026, and current Hypothesis releases need 3.11. The CI matrix
  is 3.11 to 3.14, ruff and mypy target 3.11, the `tomli` backport and
  the 3.10 `tomllib` fallback in `scripts/check_suite_consistency.py` are
  gone, and `requirements/ci.txt` and `build.txt` are compiled for 3.11.
  `ci.txt` now pins one Hypothesis (6.170.8) and drops the 3.10-era
  websockets 16.1.1, rpds-py 0.30.0 and starlette 1.7.0 pins; starlette
  is 1.10.0 in `ci.txt` and `fuzz.txt`. On 3.10, pip keeps resolving
  0.0.23.

### Security

- `requirements/audit.txt`, the hash-pinned pip-audit for the CI audit
  job, pinned filelock 4.1.0 on Python 3.10 (GHSA-9vhv-jxww-xfm5,
  GHSA-567q-5qvw-pf92, GHSA-v4x8-3wr5-3wq8). Only that job installs it,
  on Python 3.12, so `audit.in` floors `filelock >= 4.2.1` and the tree is
  compiled for 3.12.

### Changed

- `requirements/ci.in` floors `ruff >= 0.17.2`, and `ci.txt` moves
  hypothesis to 6.170.8 on Python 3.11+ (6.168.5 stays on 3.10, the last
  release that supports it), in place of Dependabot #16 and #17. Their
  recompiles were not universal and failed the Python 3.10 tests, and
  #15's had already dropped the per-Python markers from `ci.txt`; the
  universal compile restores them.

## [0.0.23] - 2026-10-20

Suite release with `camt053` 0.0.23, which releases first. Two parser
fixes, and the gates and documents this repository was missing.

### Fixed

- **`:61:` supplementary details no longer leak into the servicer
  reference.** Line 2 of a `:61:` (subfield 9) was joined onto line 1
  before matching, so `REF1//CREF1` followed by `/OCMT/EUR500,00/` gave
  `account_servicer_ref="CREF1/OCMT/EUR500,00/"`. The reference is now
  `CREF1`, and the supplementary details are kept as the entry's first
  `TransactionDetails`, ahead of any `:86:` text. This changes the
  returned document for entries that carry a line 2: their `details`
  list gains that item at the front. Entries without one are unchanged.
- **CRLF reports parse identically to LF.** `parse_mt942` documented
  CRLF tolerance but left `\r` inside multi-line `:61:` and `:86:`
  values.
- The scheduled **Suite Consistency** job compared this tree with the
  `camt053` core's PyPI version, so mid-release (core out, this package
  bumped but not tagged) it did not report this package's missing
  release. It is now the suite's shared script, comparing the tree with
  this package's own release while still requiring every member to
  publish the core's version.
- The README rendered on PyPI said "Latest release: v0.0.14" in 0.0.16
  and 0.0.20. `scripts/verify_versions.py` now checks every version
  source, and the `camt053` floor in `pyproject.toml` and
  `requirements/*.in`, on each pull request.
- Six source files, both shipped modules among them, declared
  `Apache-2.0` only although the package is `Apache-2.0 OR MIT`. Every
  file now carries REUSE 3.3 SPDX lines, checked by `reuse lint`; the
  Apache-only trove classifier is dropped.

### Added

- A complexity gate (`scripts/check_complexity.py`, CI and `make
  complexity`): per function cyclomatic 10, cognitive 15, Halstead
  difficulty 30 and 60 lines, 500 lines per file, against
  `complexity-baseline.json`, which can only shrink. Its one entry,
  `parse_mt942`, was refactored under the ceilings (no behaviour
  change), so the baseline is empty.
- Fuzzing: an Atheris harness (`fuzz/fuzz_parse_mt942.py`, two minutes
  per change, 30 minutes weekly) and Hypothesis property tests, both
  holding `parse_mt942` to returning a document or raising `ValueError`.
- OpenSSF Scorecard, DCO, dependency-audit (`pip-audit`) and
  version-source workflows; Dependabot version updates for pip and
  GitHub Actions.
- `CITATION.cff`, `CODE_OF_CONDUCT.md`, pull request and issue
  templates, a `Makefile` whose `make check` runs every CI gate, a
  rendered demo (`make demo`), `docs/index.md`, `docs/POLICIES.md` and
  `docs/COMPARISON.md`.

### Changed

- Version aligned to `0.0.23` with the rest of the suite.
- **Requires `camt053` 0.0.23 or newer** (was 0.0.16), still below 1. The
  suite releases core first at one version, and core 0.0.23 is the first
  to floor its advised dependencies (`fastapi` 0.109.1 for PYSEC-2024-38,
  `starlette` 1.3.1, `cryptography` 50.0.0 and others); a lower floor here
  let an older core resolve, and an affected `fastapi` with it.
- Every GitHub Action is pinned by commit SHA, CI installs from
  hash-pinned `requirements/*.txt`, and the release builds with a pinned
  hatchling, attaches SLSA build provenance, signs every distribution
  with keyless sigstore (`.sig` and `.pem` on the GitHub release) and
  names the GitHub release `camt053-loader-mt942 <version>`.
- The README follows the suite template; `docs/benchmarks.md` is now
  `docs/BENCHMARKS.md`, with results measured on 2026-10-20.

## [0.0.20] - 2026-08-29

Aligns the `camt053` suite on one version number, and adds the gates this
repository was missing.

### Added

- `benches/bench_parse_mt942.py` measures parse throughput along the two
  axes that actually move: entries per report (the busy hour) and
  reports per file (many accounts polled at once). It prints a growth
  exponent for each, because a parser that has gone superlinear looks
  healthy on a ten-entry fixture and falls over on a payroll run. Both
  axes currently measure linear.
- `docs/benchmarks.md` explaining what the two axes mean and why the
  exponent is the number to read rather than `ns/entry` at the smallest
  size.
- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow comparing this tree, and every published member
  of the suite, against PyPI.
- `tests/test_suite_conformance.py`, the shared suite conformance gate.
- `SECURITY.md`, written for a parsing library: the whole attack surface
  is the untrusted text it is handed, and an intraday report's size is
  not under the caller's control.

### Changed

- Version aligned to `0.0.20` across all six `camt053` packages, which
  had drifted to `0.0.18`, `0.0.18`, `0.0.19`, `0.0.18`, `0.0.16` and
  `0.0.16`.

## [0.0.16] - 2026-08-21

Suite release with `camt053` 0.0.16. No functional change in this
package.

### Changed

- **Version aligned to the suite.** Every package in the `camt053`
  suite ships the same number, so there is no compatibility table to
  consult. See `camt053.suite`, which a daily job checks against PyPI.

- **The `camt053` floor moves to `>=0.0.16`,** from `>=0.0.6` — a bound
  that had not been revisited in nine releases, because it still
  resolved and so never complained.

### Added

- **A version-sync test.** `pyproject.toml` and `__init__.py` state the
  version independently and nothing compared them, so a release could
  ship with the two disagreeing. It nearly did: the first attempt at
  this release landed `__init__.py` at 0.0.16 against a `pyproject.toml`
  still on 0.0.14, and every check passed.

## [0.0.14] - 2026-07-16

### Fixed

- **Stress-suite worker exception handling** (`tests/test_stress.py`)
  — the concurrent-conversion worker now catches `Exception` instead
  of `BaseException`, mirroring the identical fix in `camt053` core
  (CodeQL `py/catch-base-exception`). The worker only collects
  conversion/assertion failures; `KeyboardInterrupt`/`SystemExit`
  were never meant to be swallowed.

### Changed

- **Version** — suite-wide lockstep bump to `0.0.14`, targeting the
  `0.0.14` release of `camt053`. No functional changes to the loader.

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
