# Contributing

Thanks for looking. This package is small on purpose: it turns an MT942
payload into the same `ParsedDocument` the rest of the `camt053` suite
already understands — a camt.052 interim report rather than a camt.053
statement — and nothing else.

## Before you open a pull request

Everything CI checks, you can run locally:

```sh
pip install -e ".[dev]"
pytest                                        # tests + the coverage gate
ruff check camt053_loader_mt942/ tests/ examples/ benches/ scripts/
ruff format --check camt053_loader_mt942/ tests/ examples/ benches/ scripts/
mypy camt053_loader_mt942/
python benches/bench_parse_mt942.py --quick   # the benchmark still runs
```

`pytest` fails below **100% branch coverage**. That is not a stretch goal
here — the package is a few hundred lines, and the branches that go untested
are the malformed-input ones, which is exactly where a statement parser earns
its keep.

## What the tests are for

- `tests/test_loader.py` — the parse itself, valid and malformed.
- `tests/test_stress.py` — large payloads, marked `perf` and excluded from
  the default run. Select with `pytest -m perf --no-cov`.
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

## Versioning

The version is restated in `pyproject.toml` and
`camt053_loader_mt942/__init__.py`. Change both, add a `CHANGELOG.md` entry,
and the conformance tests will confirm they agree — they exist because the
suite has already published a release whose `__version__` reported the
previous one.

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`, not `0.0.9`.

## Licence

Apache-2.0 OR MIT, at your option. By contributing you agree your work is
released under the same dual grant.
