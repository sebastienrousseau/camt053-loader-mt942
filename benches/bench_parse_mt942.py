#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Throughput of :func:`parse_mt942` as interim reports grow.

Why this and not something else: an intraday report is the one input whose
size the caller does not control. MT942 is polled -- a treasury system asks
for movements since the last poll, and how many that is depends on how busy
the account was, not on anything the caller decides. A quiet hour returns a
handful of ``:61:`` entries; the hour a payroll run lands returns thousands.
And a system polling many accounts hands over a file containing many
reports. Those are the two axes that move in practice, so they are the two
this measures.

What it is watching for is **shape, not speed**. A parser linear in entries
stays usable as the file grows; one that is quadratic -- because some lookup
rescans the entries already parsed -- looks fine on the fixtures and falls
over on the busy hour. The ``ns/entry`` column is the number to read: it
should stay roughly flat across sizes, and the growth exponent printed
underneath says the same thing in one number (1.0 is linear, 2.0 quadratic).

Read the exponent in preference to eyeballing ``ns/entry`` at small sizes.
Ten entries parse in about a tenth of a millisecond, which is close enough
to timer noise that the per-entry figure bounces around by a factor of two
between runs while telling you nothing.

Run::

    python benches/bench_parse_mt942.py
    python benches/bench_parse_mt942.py --json      # machine-readable
    python benches/bench_parse_mt942.py --quick     # what CI runs

Timings are wall-clock on one machine and are not comparable between
machines, so nothing here asserts a threshold. CI runs ``--quick`` to prove
the benchmark still executes against the current API; a benchmark that has
silently stopped compiling is worse than none, because it reads as coverage
that does not exist.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from camt053_loader_mt942 import parse_mt942  # noqa: E402


def build(entries: int, reports: int = 1) -> str:
    """An MT942 payload of ``reports`` reports, each with ``entries``.

    Entry references are distinct per entry so nothing can be collapsed
    by a cache keyed on the reference -- that would measure the cache
    rather than the parser.
    """
    documents = []
    for report in range(reports):
        lines = [
            f":20:INTRA-{report:05d}",
            ":25:COBADEFFXXX/DE89370400440532013000",
            f":28C:{report + 1}/1",
            ":34F:EURD1000,00",
            ":34F:EURC500,00",
            ":13D:2606211430+0200",
        ]
        for i in range(entries):
            marker = ("C", "D", "RC", "RD")[i % 4]
            lines.append(
                f":61:2606210621{marker}{(i + 1) * 100},25NMSC"
                f"BANKREF{i:06d}//CUSTREF{i:06d}"
            )
            lines.append(f":86:Movement {i:06d}")
        lines.append(":90D:5EUR1500,75")
        lines.append(":90C:5EUR1500,50")
        documents.append("\n".join(lines))
    return "\n".join(documents) + "\n"


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _exponent(points: list[tuple[int, float]]) -> float | None:
    """Log-log slope across the measured range: 1.0 linear, 2.0 quadratic."""
    if len(points) < 2:
        return None
    (n0, t0), (n1, t1) = points[0], points[-1]
    if n0 == n1 or t0 <= 0 or t1 <= 0:
        return None
    return math.log(t1 / t0) / math.log(n1 / n0)


def measure_entries(sizes: list[int], repeats: int) -> dict:
    """One report, growing entry count: the busy-hour axis."""
    rows, points = [], []
    for count in sizes:
        text = build(count)
        seconds = _best(lambda t=text: parse_mt942(t), repeats)
        points.append((count, seconds))
        rows.append(
            {
                "entries": count,
                "ms": seconds * 1e3,
                "ns_per_entry": seconds * 1e9 / count,
                "bytes": len(text),
            }
        )
    return {"rows": rows, "exponent": _exponent(points)}


def measure_reports(counts: list[int], entries: int, repeats: int) -> dict:
    """Many reports in one file: the many-accounts axis."""
    rows, points = [], []
    for count in counts:
        text = build(entries, reports=count)
        seconds = _best(lambda t=text: parse_mt942(t), repeats)
        points.append((count, seconds))
        rows.append(
            {
                "reports": count,
                "ms": seconds * 1e3,
                "us_per_report": seconds * 1e6 / count,
            }
        )
    return {"rows": rows, "exponent": _exponent(points), "entries": entries}


def run(quick: bool) -> dict:
    entry_sizes = [10, 100] if quick else [10, 100, 1_000, 5_000]
    report_counts = [1, 10] if quick else [1, 10, 50, 200]
    repeats = 2 if quick else 5
    return {
        "by_entries": measure_entries(entry_sizes, repeats),
        "by_reports": measure_reports(report_counts, 20, repeats),
    }


def _shape(exponent: float | None) -> str:
    if exponent is None:
        return "not enough sizes to say"
    if exponent < 1.25:
        return "linear, as it should be"
    if exponent < 1.75:
        return "superlinear -- something is rescanning"
    return "quadratic -- a lookup is rescanning what is already parsed"


def render(results: dict) -> None:
    entries = results["by_entries"]
    print("  One report, growing entry count -- the busy-hour axis:\n")
    print(f"    {'entries':>9}{'ms':>10}{'ns/entry':>12}{'bytes':>12}")
    for row in entries["rows"]:
        print(
            f"    {row['entries']:>9}{row['ms']:>10.2f}"
            f"{row['ns_per_entry']:>12.0f}{row['bytes']:>12,}"
        )
    exponent = entries["exponent"]
    print(
        f"\n    growth exponent {exponent:.2f} -- {_shape(exponent)}."
        if exponent is not None
        else "\n    growth exponent: not enough sizes."
    )

    reports = results["by_reports"]
    print(
        f"\n  Many reports in one file ({reports['entries']} entries each) "
        f"-- the many-accounts axis:\n"
    )
    print(f"    {'reports':>9}{'ms':>10}{'us/report':>13}")
    for row in reports["rows"]:
        print(
            f"    {row['reports']:>9}{row['ms']:>10.2f}"
            f"{row['us_per_report']:>13.1f}"
        )
    exponent = reports["exponent"]
    print(
        f"\n    growth exponent {exponent:.2f} -- {_shape(exponent)}."
        if exponent is not None
        else "\n    growth exponent: not enough sizes."
    )
    print(
        "\n  Read the exponent rather than ns/entry at the smallest size: "
        "ten entries parse in\n  well under a millisecond, close enough to "
        "timer noise that the per-entry figure moves\n  by a factor of two "
        "between runs while meaning nothing."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
