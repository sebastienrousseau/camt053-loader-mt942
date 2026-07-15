# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Load / stress suite for the MT942 → camt.052 converter.

Three production-shaped workloads, mirroring the suite-wide convention
set by the camt053 parent project (``perf``-marked, excluded from the
100% coverage gate, run explicitly with ``--no-cov``):

* **Sustained concurrent load** — 32 worker threads convert a
  representative MT942 interim report for several hundred total
  iterations; the test asserts zero errors and a generous p95
  per-conversion latency ceiling.
* **Large input** — a single MT942 carrying thousands of ``:61:``
  statement lines parses correctly within a generous wall-clock bound.
* **Soak / memory** — a long conversion loop must not leak: traced
  memory growth (``tracemalloc``) stays under a small fixed budget.

All latency/memory ceilings are deliberately loose (10×+ headroom over
observed laptop numbers) so the suite catches order-of-magnitude
regressions without flaking on slow or noisy CI runners. Run locally
with::

    pytest tests/test_stress.py -m perf --no-cov
"""

from __future__ import annotations

import gc
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

import pytest
from camt053.models import ParsedDocument

from camt053_loader_mt942 import parse_mt942

# ─── Workload parameters ─────────────────────────────────────────────────────

#: Concurrent workers for the sustained-load test. 32 threads is well
#: past the point where CPython's GIL serialises the pure-Python parse,
#: so the test exercises real lock contention, not just a happy path.
_WORKERS = 32

#: Conversions per worker in the sustained-load test (32 × 20 = 640
#: total conversions — "several hundred iterations").
_ITERATIONS_PER_WORKER = 20

#: Generous p95 per-conversion latency ceiling under full contention.
#: Observed p95 on a developer laptop is well under 10 ms; 250 ms only
#: trips on an order-of-magnitude regression.
_P95_CEILING_SECONDS = 0.250

#: Statement lines in the large-input test (each with an :86: detail).
_LARGE_ENTRY_COUNT = 5_000

#: Generous wall-clock bound for parsing the large input once.
_LARGE_PARSE_CEILING_SECONDS = 10.0

#: Iterations in the soak loop.
_SOAK_ITERATIONS = 500

#: Traced-memory growth budget for the soak loop. A leak of one
#: retained ParsedDocument per iteration would blow through this
#: within a few dozen iterations; steady-state growth is near zero.
_SOAK_GROWTH_BUDGET_BYTES = 5 * 1024 * 1024


# ─── Payload builders ────────────────────────────────────────────────────────


def _representative_mt942() -> str:
    """Return a representative MT942 covering every supported tag.

    Ten movements (credits, debits, and a reversal pair), each with an
    ``:86:`` information line — a realistic intraday interim report.
    """
    lines = [
        ":20:INTRA-STRESS-1",
        ":25:COBADEFFXXX/DE89370400440532013000",
        ":28C:42/1",
        ":34F:EURD1000,00",
        ":34F:EURC500,00",
        ":13D:2606211430+0200",
    ]
    for i in range(10):
        dc = ("C", "D", "RC", "RD")[i % 4]
        lines.append(
            f":61:2606210621{dc}{(i + 1) * 100},25NMSC"
            f"BANKREF{i:03d}//CUSTREF{i:03d}"
        )
        lines.append(f":86:Stress movement {i:03d}")
    lines.append(":90D:5EUR1500,75")
    lines.append(":90C:5EUR1500,50")
    return "\n".join(lines) + "\n"


def _mt942_with_entries(entry_count: int) -> str:
    """Return an MT942 payload with ``entry_count`` statement lines."""
    header = (
        ":20:INTRA-LARGE-1\n"
        ":25:COBADEFFXXX/DE89370400440532013000\n"
        ":28C:99/1\n"
        ":34F:EURD1000,00\n"
        ":13D:2606211430+0200\n"
    )
    body = "".join(
        f":61:2606210621{'C' if i % 2 == 0 else 'D'}{(i % 997) + 1},00NMSC"
        f"REF{i:06d}//CREF{i:06d}\n"
        f":86:Bulk movement {i:06d}\n"
        for i in range(entry_count)
    )
    footer = ":90D:2500EUR12345,67\n:90C:2500EUR12345,89\n"
    return header + body + footer


def _convert_once(payload: str) -> ParsedDocument:
    """Run one full conversion (parse + to_dict round trip)."""
    doc = parse_mt942(payload)
    doc.to_dict()
    return doc


# ─── Sustained concurrent load ───────────────────────────────────────────────


@pytest.mark.perf
def test_sustained_concurrent_conversions_zero_errors_and_p95() -> None:
    """640 conversions across 32 threads: zero errors, sane p95 latency.

    Every worker converts the representative interim report
    ``_ITERATIONS_PER_WORKER`` times and validates the output document
    on each pass; any exception or wrong-shape result fails the test.
    The p95 of per-conversion wall-clock latency (measured under full
    thread contention) must stay under the generous ceiling.
    """
    payload = _representative_mt942()
    errors: list[BaseException] = []
    latencies: list[float] = []

    def _worker() -> None:
        """Convert the payload repeatedly, recording latency/errors."""
        for _ in range(_ITERATIONS_PER_WORKER):
            started = time.perf_counter()
            try:
                doc = _convert_once(payload)
                assert doc.message_type == "camt.052.001.08"
                assert doc.msg_id == "INTRA-STRESS-1"
                assert len(doc.statements[0].entries) == 10
            except BaseException as exc:  # noqa: B036 - stress harness
                errors.append(exc)
            finally:
                latencies.append(time.perf_counter() - started)

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        futures = [pool.submit(_worker) for _ in range(_WORKERS)]
        for future in futures:
            future.result()

    total = _WORKERS * _ITERATIONS_PER_WORKER
    assert len(latencies) == total
    assert not errors, f"{len(errors)} conversion(s) failed: {errors[:3]!r}"

    p95 = sorted(latencies)[int(0.95 * total) - 1]
    print(
        f"\nsustained load: {total} conversions, {_WORKERS} workers, "
        f"p95 {p95 * 1000:.2f} ms "
        f"(ceiling {_P95_CEILING_SECONDS * 1000:.0f} ms)"
    )
    assert p95 <= _P95_CEILING_SECONDS, (
        f"p95 conversion latency {p95 * 1000:.1f} ms exceeded the "
        f"{_P95_CEILING_SECONDS * 1000:.0f} ms ceiling — an "
        f"order-of-magnitude regression, not runner noise."
    )


# ─── Large input ─────────────────────────────────────────────────────────────


@pytest.mark.perf
def test_large_report_parses_within_wall_clock_bound() -> None:
    """A 5,000-line MT942 parses correctly inside the wall-clock bound.

    Correctness is asserted alongside speed: entry count, per-entry
    :86: detail attachment, and the summary balances must all survive
    the bulk payload.
    """
    payload = _mt942_with_entries(_LARGE_ENTRY_COUNT)

    started = time.perf_counter()
    doc = parse_mt942(payload)
    elapsed = time.perf_counter() - started

    statement = doc.statements[0]
    assert len(statement.entries) == _LARGE_ENTRY_COUNT
    assert statement.entries[0].reference == "REF000000"
    assert statement.entries[-1].details[0].additional_info == (
        f"Bulk movement {_LARGE_ENTRY_COUNT - 1:06d}"
    )
    assert len(statement.balances) == 3  # 1 floor limit + 2 summaries

    print(
        f"\nlarge input: {_LARGE_ENTRY_COUNT} entries "
        f"({len(payload) / 1_000_000:.2f} MB) parsed in {elapsed:.3f} s "
        f"(ceiling {_LARGE_PARSE_CEILING_SECONDS:.0f} s)"
    )
    assert elapsed <= _LARGE_PARSE_CEILING_SECONDS, (
        f"Large-input parse took {elapsed:.2f} s, exceeding the "
        f"{_LARGE_PARSE_CEILING_SECONDS:.0f} s ceiling."
    )


# ─── Soak / memory growth ────────────────────────────────────────────────────


@pytest.mark.perf
def test_soak_loop_memory_growth_is_bounded() -> None:
    """500 back-to-back conversions leak no meaningful memory.

    After a warm-up pass (regex caches, camt053 model internals), the
    traced-memory level at the end of the soak loop must sit within a
    small fixed budget of the post-warm-up level.
    """
    payload = _representative_mt942()

    # Warm up import-time and first-call allocations outside the
    # measured window.
    for _ in range(20):
        _convert_once(payload)

    gc.collect()
    tracemalloc.start()
    try:
        baseline, _ = tracemalloc.get_traced_memory()

        for _ in range(_SOAK_ITERATIONS):
            _convert_once(payload)

        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    growth = current - baseline
    print(
        f"\nsoak: {_SOAK_ITERATIONS} iterations, growth "
        f"{growth / 1024:.1f} KiB (budget "
        f"{_SOAK_GROWTH_BUDGET_BYTES / 1024:.0f} KiB), "
        f"peak {peak / 1024:.1f} KiB"
    )
    assert growth <= _SOAK_GROWTH_BUDGET_BYTES, (
        f"Traced memory grew by {growth} bytes over {_SOAK_ITERATIONS} "
        f"iterations (budget {_SOAK_GROWTH_BUDGET_BYTES}); the "
        f"converter is retaining per-conversion state."
    )
