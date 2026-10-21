<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

`parse_mt942` is handed the one input whose size the caller does not
control. MT942 is *polled*: a treasury system asks for movements since
the last poll, and how many that is depends on how busy the account was,
not on anything the caller decides. A quiet hour returns a handful of
`:61:` entries; the hour a payroll run lands returns thousands.

## Running it

```sh
python benches/bench_parse_mt942.py           # full run
python benches/bench_parse_mt942.py --quick   # what CI runs
python benches/bench_parse_mt942.py --json    # machine-readable
```

CI runs `--quick`. That is not a timing gate — wall-clock is not
comparable between runners, and a flaky performance gate teaches people
to ignore red. It runs so a benchmark that has stopped compiling against
the current API fails the build rather than rotting into a file that
reads as coverage which does not exist.

## The two axes

**Entries per report** — the busy-hour axis. One report, growing entry
count.

**Reports per file** — the many-accounts axis. A system polling many
accounts hands over one file containing many reports.

Both should be linear. The benchmark prints a growth exponent for each:
1.0 is linear, 2.0 quadratic. A parser that goes superlinear — because
some lookup rescans the entries already parsed — looks perfectly healthy
on a fixture of ten entries and falls over on the busy hour.

## Results

Measured with `python benches/bench_parse_mt942.py` on 2026-10-20 (Apple
A18 Pro, Python 3.12.15, camt053 0.0.20):

| Entries per report | ms | ns/entry |
| ---: | ---: | ---: |
| 10 | 0.09 | 8,971 |
| 100 | 0.56 | 5,585 |
| 1,000 | 6.32 | 6,316 |
| 5,000 | 34.68 | 6,936 |

Growth exponent 0.96: linear.

| Reports per file (20 entries each) | ms | us/report |
| ---: | ---: | ---: |
| 1 | 0.13 | 125.1 |
| 10 | 1.28 | 127.7 |
| 50 | 8.21 | 164.2 |
| 200 | 31.61 | 158.0 |

Growth exponent 1.04: linear. The 0.0.20 release measured 1.00 and 1.09
on the same two axes.

## Reading the output

Read the **exponent**, not `ns/entry` at the smallest size. Ten entries
parse in well under a millisecond, close enough to timer noise that the
per-entry figure moves by a factor of two between runs while meaning
nothing. The exponent is measured across the whole range and is the
stable signal.
