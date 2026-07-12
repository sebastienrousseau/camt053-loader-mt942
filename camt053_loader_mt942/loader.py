# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""MT942 → camt.052 ParsedDocument loader.

SWIFT MT942 is the *Interim Transaction Report*: the intraday sibling
of the MT940 end-of-day statement. Where MT940 maps to camt.053
(Bank-to-Customer Statement), MT942 maps to **camt.052**
(Bank-to-Customer Account **Report**). The ``camt053`` typed model is
message-type-agnostic — its :class:`~camt053.models.Statement` doubles
as a camt.052 ``<Rpt>`` container — so an MT942 payload lands in the
exact same :class:`~camt053.models.ParsedDocument` shape, only with
``message_type="camt.052.001.08"``.

The MT942 grammar handled here is the common-denominator subset
shipped by EU and UK commercial banks:

* ``:20:``  Transaction reference number (mandatory)
* ``:25:``  Account identification (mandatory; optional BIC prefix)
* ``:28C:`` Statement / sequence number (mandatory)
* ``:34F:`` Floor limit indicator (debit, and optionally credit)
* ``:13D:`` Date/time indication — the interim report timestamp
* ``:61:``  Statement line (one per movement, repeatable)
* ``:86:``  Information to account owner (attaches to the prior ``:61:``)
* ``:90D:`` Number and sum of debit entries (summary)
* ``:90C:`` Number and sum of credit entries (summary)

Interim-report specifics vs MT940
----------------------------------
MT942 carries **no booked opening/closing balances** (``:60F:`` /
``:62F:``). Instead it carries *floor limits* (``:34F:``) — the
threshold above which movements are reported — and *entry-count
summaries* (``:90D:`` / ``:90C:``). The ``camt053`` typed model has no
dedicated field for either (it is camt.053-statement-oriented: it
models ``<Bal>`` but not camt.052's ``<Lmt>`` floor-limit block or its
``<TxsSummry>`` transaction-summary block). Rather than invent fields
or silently drop data, this loader surfaces both on the
:class:`~camt053.models.Balance` list using **clearly proprietary
``type_code`` values** so downstream consumers can recognise and
filter them out:

* ``:34F:`` floor limit  → ``Balance(type_code="FLIMD" | "FLIMC")``
  (Floor LIMit, Debit / Credit variant).
* ``:90D:`` debit summary  → ``Balance(type_code="SUMD:<count>")``
* ``:90C:`` credit summary → ``Balance(type_code="SUMC:<count>")``

For the ``:90x:`` summaries the *sum* is carried in
:attr:`~camt053.models.Balance.amount` and the ISO ``NbOfNtries``
*count* is encoded into the ``type_code`` (after the colon), because
the typed model has no integer count field. This is a documented
limitation of representing a camt.052 interim report in a
camt.053-oriented model — see the package README.

Reversal detection: an MT942 ``:61:`` line whose debit/credit
indicator is ``RD`` (reversal debit) or ``RC`` (reversal credit) is
mapped to an :class:`~camt053.models.Entry` with
``reversal_indicator=True`` — identical to the MT940 loader.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from camt053.models import (
    Account,
    Balance,
    Entry,
    ParsedDocument,
    Statement,
    TransactionDetails,
)

__all__ = ["parse_mt942"]

# The message type this loader produces: the camt.052 Bank-to-Customer
# Account Report, at the ``.001.08`` maintenance variant — the direct
# camt.052 analog of the MT940 loader's ``camt.053.001.08`` output and
# a CBPR+ current schema version in ``camt053``.
MESSAGE_TYPE = "camt.052.001.08"


# ─── Mapping tables ──────────────────────────────────────────────────────────

# MT942 debit/credit indicators on :61: lines:
# C  = Credit, D  = Debit
# RC = Reversal of credit, RD = Reversal of debit
_DC_TO_CAMT = {
    "C": ("CRDT", False),
    "D": ("DBIT", False),
    "RC": ("CRDT", True),
    "RD": ("DBIT", True),
}


# ─── Regex helpers ───────────────────────────────────────────────────────────

# A field starts with :tag: at the beginning of a line. Tags are 2-3
# chars, optionally followed by a single letter (e.g. 34F, 28C, 90D).
_FIELD_HEAD_RE = re.compile(r"^:(\d{2}[A-Z]?):", re.MULTILINE)

# :61:2606210621D1000,00N123ABC//REF1
#     ^vYYMMDD ^bMMDD (opt) ^DC ^Amt (comma-decimal)
#     ^TxCode ^Ref [+ opt //Customer ref]
_LINE_RE = re.compile(
    r"^(?P<vdate>\d{6})"
    r"(?P<bdate>\d{4})?"
    r"(?P<dc>RC|RD|C|D)"
    r"(?P<fund_code>[A-Z])?"
    r"(?P<amt>[\d,]+)"
    r"(?P<txcode>[A-Z][A-Z0-9]{3})"
    r"(?P<rest>.*)$"
)

# :34F:EUR D1000,00  or  :34F:EURD1000,00  or  :34F:EUR1000,00
#       ^CCY ^optional D/C mark ^Amount (comma-decimal)
# The D/C mark is optional; when absent the limit applies to both
# debit and credit movements (SWIFT MT942 spec, field 34F).
_FLOOR_RE = re.compile(r"^(?P<ccy>[A-Z]{3})(?P<dc>[DC])?(?P<amt>[\d,]+)$")

# :90D:12EUR1234,56  →  ^count ^CCY ^Sum (comma-decimal)
_SUMMARY_RE = re.compile(r"^(?P<count>\d+)(?P<ccy>[A-Z]{3})(?P<amt>[\d,]+)$")


# ─── Tokeniser ──────────────────────────────────────────────────────────────


def _iter_fields(text: str) -> Iterator[tuple[str, str]]:
    """Yield ``(tag, value)`` pairs from an MT942 payload.

    Values may span multiple lines; everything after a ``:tag:`` head
    up to (but not including) the next ``:tag:`` head is the value,
    with the leading tag stripped and trailing whitespace normalised.
    """
    matches = list(_FIELD_HEAD_RE.finditer(text))
    for index, match in enumerate(matches):
        tag = match.group(1)
        value_start = match.end()
        value_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        value = text[value_start:value_end].strip()
        yield tag, value


# ─── Field parsers ──────────────────────────────────────────────────────────


def _parse_floor_limit(value: str) -> Balance:
    """Parse a :34F: floor-limit field into a proprietary Balance.

    The floor limit is surfaced as a :class:`~camt053.models.Balance`
    with ``type_code="FLIMD"`` (debit) or ``"FLIMC"`` (credit) because
    the typed model has no camt.052 ``<Lmt>`` floor-limit structure.
    A :34F: with no explicit ``D``/``C`` mark applies to debits.
    """
    match = _FLOOR_RE.match(value.replace(" ", ""))
    if not match:
        raise ValueError(f"Malformed floor-limit field :34F:{value!r}")
    dc = match.group("dc") or "D"
    return Balance(
        type_code="FLIMC" if dc == "C" else "FLIMD",
        amount=match.group("amt").replace(",", "."),
        currency=match.group("ccy"),
        credit_debit_indicator="CRDT" if dc == "C" else "DBIT",
        date=None,
    )


def _parse_summary(value: str, tag: str) -> Balance:
    """Parse a :90D:/:90C: entry-summary field into a proprietary Balance.

    The *sum* is carried in :attr:`~camt053.models.Balance.amount`; the
    ISO ``NbOfNtries`` *count* is encoded into ``type_code`` after a
    colon (``"SUMD:<n>"`` / ``"SUMC:<n>"``) because the typed model has
    no camt.052 ``<TxsSummry>`` structure to hold an integer count.
    """
    match = _SUMMARY_RE.match(value)
    if not match:
        raise ValueError(f"Malformed summary field :{tag}:{value!r}")
    dc = "C" if tag == "90C" else "D"
    return Balance(
        type_code=f"SUM{dc}:{int(match.group('count'))}",
        amount=match.group("amt").replace(",", "."),
        currency=match.group("ccy"),
        credit_debit_indicator="CRDT" if dc == "C" else "DBIT",
        date=None,
    )


def _parse_entry(value: str) -> Entry:
    """Parse a :61: statement line into an :class:`~camt053.models.Entry`."""
    # Reference details after the amount/code can be split on `//`
    # (bank ref // customer ref). Both halves are optional.
    match = _LINE_RE.match(value.replace("\n", ""))
    if not match:
        raise ValueError(f"Malformed :61: statement line {value!r}")
    indicator, is_reversal = _DC_TO_CAMT[match.group("dc")]
    rest = match.group("rest") or ""
    bank_ref, _, customer_ref = rest.partition("//")
    return Entry(
        reference=bank_ref.strip() or None,
        amount=match.group("amt").replace(",", "."),
        credit_debit_indicator=indicator,
        status="BOOK",
        booking_date=_format_yymmdd_with_year_hint(
            match.group("bdate"), match.group("vdate")
        ),
        value_date=_format_yymmdd(match.group("vdate")),
        account_servicer_ref=customer_ref.strip() or None,
        reversal_indicator=is_reversal,
    )


def _parse_account(value: str) -> Account:
    """Parse a :25: account-identification field.

    The field is ``[BIC/]<account>`` where the BIC prefix is optional
    and separated by a forward slash.
    """
    bic: str | None
    account: str
    if "/" in value:
        bic, _, account = value.partition("/")
        bic = bic.strip() or None
        account = account.strip()
    else:
        bic = None
        account = value.strip()
    # IBANs are 15-34 chars and start with two letters + two digits;
    # anything else is treated as a proprietary identifier.
    is_iban = bool(re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", account))
    return Account(
        iban=account if is_iban else None,
        other_id=None if is_iban else account or None,
        servicer_bic=bic,
    )


def _parse_datetime_indication(value: str) -> str | None:
    """Parse a :13D: date/time indication into an ISO-8601 timestamp.

    The MT942 :13D: format is ``YYMMDDHHMM±HHMM`` (local time plus a
    UTC offset). It is surfaced as the report's ``creation_date_time``
    in ISO-8601 form, e.g. ``2026-06-21T14:30:00+02:00``. A malformed
    value yields ``None`` rather than aborting the parse.
    """
    match = re.match(
        r"^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([+-]\d{2})(\d{2})$",
        value.strip(),
    )
    if not match:
        return None
    yy, mm, dd, hh, mi, off_h, off_m = match.groups()
    date = _format_yymmdd(yy + mm + dd)
    return f"{date}T{hh}:{mi}:00{off_h}:{off_m}"


def _format_yymmdd(value: str) -> str:
    """Format a 6-char ``YYMMDD`` date as ISO ``YYYY-MM-DD``.

    Years are interpreted with a sliding window: 00-79 → 20YY, 80-99 →
    19YY. This matches SWIFT industry practice and is correct for any
    real report date in the 1980-2079 range.
    """
    year = int(value[0:2])
    century = 2000 if year < 80 else 1900
    return f"{century + year:04d}-{value[2:4]}-{value[4:6]}"


def _format_yymmdd_with_year_hint(
    booking_mmdd: str | None,
    value_yymmdd: str,
) -> str | None:
    """Format the booking date, borrowing the year from the value date.

    MT942 :61: lines carry a 6-char value date (YYMMDD) and an
    optional 4-char booking date (MMDD); the booking date inherits
    its year from the value date.
    """
    if booking_mmdd is None:
        return None
    return _format_yymmdd(value_yymmdd[0:2] + booking_mmdd)


# ─── Top-level parser ───────────────────────────────────────────────────────


def parse_mt942(text: str) -> ParsedDocument:
    """Parse an MT942 payload into a :class:`~camt053.models.ParsedDocument`.

    Args:
        text: The MT942 payload as a string. Trailing whitespace and
            CRLF/LF differences are tolerated.

    Returns:
        A :class:`~camt053.models.ParsedDocument` whose ``message_type``
        is ``"camt.052.001.08"`` — the camt.052 Bank-to-Customer
        Account Report, the interim-report analog of the MT940 loader's
        camt.053 output. Floor limits (``:34F:``) and entry summaries
        (``:90D:`` / ``:90C:``) are surfaced as proprietary-``type_code``
        balances (see the module docstring); the ``:13D:`` timestamp
        becomes the report ``creation_date_time``.

    Raises:
        ValueError: If a mandatory field (``:20:``, ``:25:``, ``:28C:``)
            is missing, or a floor-limit / summary / statement line does
            not match the expected format. The error message identifies
            the offending field.
    """
    statement = Statement()
    msg_id: str | None = None
    creation_dt: str | None = None
    have_account = False
    have_seq = False
    last_entry: Entry | None = None

    for tag, value in _iter_fields(text):
        if tag == "20":
            msg_id = value or None
        elif tag == "25":
            statement.account = _parse_account(value)
            have_account = True
        elif tag == "28C":
            statement.electronic_seq_nb = value
            statement.id = value
            have_seq = True
        elif tag == "13D":
            creation_dt = _parse_datetime_indication(value)
            statement.creation_date_time = creation_dt
        elif tag == "34F":
            statement.balances.append(_parse_floor_limit(value))
        elif tag in {"90D", "90C"}:
            statement.balances.append(_parse_summary(value, tag))
        elif tag == "61":
            entry = _parse_entry(value)
            statement.entries.append(entry)
            last_entry = entry
        elif tag == "86":
            _attach_additional_info(last_entry, value)
        # Unknown tags are silently ignored so future SWIFT additions
        # do not break parsing; the loader follows Postel's law here.

    if msg_id is None:
        raise ValueError("MT942 payload missing required :20: reference")
    if not have_account:
        raise ValueError("MT942 payload missing required :25: account")
    if not have_seq:
        raise ValueError("MT942 payload missing required :28C: sequence number")

    return ParsedDocument(
        message_type=MESSAGE_TYPE,
        msg_id=msg_id,
        creation_date_time=creation_dt,
        statements=[statement],
    )


def _attach_additional_info(entry: Entry | None, value: str) -> None:
    """Attach :86: free-form info to the most recent entry as a detail."""
    if entry is None:
        # An :86: with no preceding :61: is malformed in practice but
        # not actively harmful; ignore it rather than aborting the
        # whole parse.
        return
    entry.details.append(TransactionDetails(additional_info=value))
