# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Property-based fuzzing of ``parse_mt942``.

The payload comes from a bank or a correspondent and is untrusted. Whatever
it holds, the parser either returns a ``ParsedDocument`` or raises
``ValueError`` naming the field; any other exception is a crash. The
strategies build reports from real tags with hostile values, so parsing is
reached rather than rejected at the first line. The coverage-guided
counterpart is ``fuzz/fuzz_parse_mt942.py``.
"""

from __future__ import annotations

import contextlib

import pytest
from camt053.models import ParsedDocument
from hypothesis import given, settings
from hypothesis import strategies as st

from camt053_loader_mt942 import parse_mt942

FUZZ = settings(max_examples=400, deadline=None)

TAGS = ("20", "25", "28C", "34F", "13D", "61", "86", "90D", "90C", "99")
VALUES = st.one_of(
    st.text(max_size=60),
    st.from_regex(
        r"\A\d{6}(\d{4})?(RC|RD|C|D)[A-Z]?[\d,]{1,12}[A-Z][A-Z0-9]{3}.{0,30}\Z"
    ),
    st.from_regex(r"\A[A-Z]{3}[DC]?[\d, ]{1,12}\Z"),
    st.from_regex(r"\A\d{1,5}[A-Z]{3}[\d,]{1,12}\Z"),
    st.from_regex(r"\A\d{10}[+-]\d{4}\Z"),
)
FIELD = st.tuples(st.sampled_from(TAGS), VALUES).map(
    lambda field: f":{field[0]}:{field[1]}"
)
HEADER = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n"
ENDINGS = st.sampled_from(["\n", "\r\n"])


def _parse(text: str) -> None:
    with contextlib.suppress(ValueError):
        assert isinstance(parse_mt942(text), ParsedDocument)


@FUZZ
@given(text=st.text(max_size=400))
def test_arbitrary_text_parses_or_raises_valueerror(text: str) -> None:
    _parse(text)


@FUZZ
@given(fields=st.lists(FIELD, max_size=12), ending=ENDINGS)
def test_hostile_fields_parse_or_raise_valueerror(
    fields: list[str], ending: str
) -> None:
    _parse((HEADER + "\n".join(fields)).replace("\n", ending))


@pytest.mark.parametrize("tag", ["34F", "61", "90D", "90C"])
def test_a_malformed_field_names_itself(tag: str) -> None:
    with pytest.raises(ValueError, match=tag):
        parse_mt942(f"{HEADER}:{tag}:not a value\n")
