# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Coverage-guided fuzzing of ``parse_mt942`` with Atheris.

Each input becomes a report built from real MT942 tags with fuzzed values,
optionally behind a valid header so parsing gets past the mandatory
fields, in LF or CRLF; or, on one input in four, raw fuzzed text. The tags
are picked rather than discovered because the parser splits fields with a
regex and dispatches through a dict, neither of which gives libFuzzer a
comparison to learn ``:61:`` from. The parser must return a
``ParsedDocument`` or raise ``ValueError``; anything else is a crash
libFuzzer reports and minimises.

Run (Linux x86_64)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_parse_mt942.py -max_total_time=60
"""

import sys

import atheris

with atheris.instrument_imports():
    from camt053_loader_mt942 import parse_mt942

HEADER = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n"
TAGS = ["20", "25", "28C", "34F", "13D", "61", "86", "90D", "90C", "99"]


def _report(fdp: atheris.FuzzedDataProvider) -> str:
    """A report from picked tags and fuzzed values."""
    fields = [
        f":{fdp.PickValueInList(TAGS)}:{fdp.ConsumeUnicodeNoSurrogates(80)}"
        for _ in range(fdp.ConsumeIntInRange(0, 16))
    ]
    text = (HEADER if fdp.ConsumeBool() else "") + "\n".join(fields)
    return text.replace("\n", "\r\n") if fdp.ConsumeBool() else text


def test_one_input(data: bytes) -> None:
    """Parse one fuzzed report."""
    fdp = atheris.FuzzedDataProvider(data)
    if fdp.ConsumeIntInRange(0, 3) == 0:
        text = fdp.ConsumeUnicodeNoSurrogates(sys.maxsize)
    else:
        text = _report(fdp)
    try:
        parse_mt942(text)
    except ValueError:
        return


def main() -> None:
    """Hand the harness to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
