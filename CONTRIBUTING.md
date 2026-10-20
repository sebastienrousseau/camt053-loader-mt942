<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package is small on purpose: it turns an MT942
payload into the same `ParsedDocument` the rest of the `camt053` suite
already understands — a camt.052 interim report rather than a camt.053
statement — and nothing else.

## Before you open a pull request

Everything CI checks, you can run locally, inside a virtualenv:

```sh
make dev      # hash-pinned toolchain from requirements/ci.txt, package editable
make check    # every gate below, in CI's order
```

`make check` runs ruff (lint and format), mypy in strict mode, the tests with
the coverage gate, the 100% docstring gate (interrogate), the complexity
ceilings, `reuse lint`, `scripts/verify_versions.py`, the benchmark and the
examples. `make help` lists each target on its own.

`pytest` fails below **100% branch coverage**. That is not a stretch goal
here — the package is a few hundred lines, and the branches that go untested
are the malformed-input ones, which is exactly where a statement parser earns
its keep.

## What the tests are for

- `tests/test_loader.py` — the parse itself, valid and malformed.
- `tests/test_stress.py` — large payloads, marked `perf` and excluded from
  the default run. Select with `pytest -m perf --no-cov`.
- `tests/test_check_complexity.py`, `tests/test_check_suite_consistency.py`
  and `tests/test_verify_versions.py` — the repository's own gates, so a gate
  that stops catching anything fails here first.
- `tests/test_suite_conformance.py` — shared across all 32 repositories in
  the suite. **Do not edit it here.** It is generated from one canonical copy,
  and a local edit fails `test_this_file_is_the_canonical_copy` by design;
  the point is that no repository can quietly weaken a shared gate.

## Benchmarks

`benches/` measures throughput as statements grow. It asserts nothing —
wall-clock numbers are not comparable between machines — but CI runs it with
`--quick` so a benchmark that has stopped compiling against the current API
fails the build rather than rotting unnoticed.

Read the `ns/entry` column. Flat across sizes means linear. A number that
climbs with size means the parser has gone superlinear, which no unit test
will tell you and a month-end statement file will.

## Complexity

Every function stays within cyclomatic complexity 10, cognitive complexity
15, Halstead difficulty 30 and 60 lines, and every file within 500 lines
(`scripts/check_complexity.py`). Offenders that predate the gate live in
`complexity-baseline.json`, which may only shrink: a new offender, or a
baselined one getting worse, fails CI. After an improvement, run
`python scripts/check_complexity.py --update` and commit the smaller
baseline with it.

## Dependencies

CI installs from the hash-pinned `requirements/*.txt`. Change the `.in`
file beside it (and the `dev` extra in `pyproject.toml`, which states the
same floors), then regenerate with the command in the `.in` file's header.

## Versioning

The version is restated in `pyproject.toml`,
`camt053_loader_mt942/__init__.py`, `CHANGELOG.md`, `releases/v<version>.md`,
`CITATION.cff`, the README's "Latest release" line and `SECURITY.md`.
`scripts/verify_versions.py` fails CI when any of them disagrees; it exists
because the README told PyPI "Latest release: v0.0.14" for two releases.

The suite releases together at one version, the `camt053` core first.

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`, not `0.0.9`.

## Commits

Conventional Commit subjects (`fix:`, `feat:`, `docs:`...), signed commits,
and a `Signed-off-by:` line (`git commit -s`) certifying the
[Developer Certificate of Origin](https://developercertificate.org/).
Pull requests follow `.github/PULL_REQUEST_TEMPLATE.md` and the
[code of conduct](CODE_OF_CONDUCT.md) applies.

## Licence

Apache-2.0 OR MIT, at your option. By contributing you agree your work is
released under the same dual grant. Every file carries SPDX lines; `reuse
lint` checks them.
