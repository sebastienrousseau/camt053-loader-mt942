# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Tests for the camt053-loader-mt942 loader."""

from __future__ import annotations

import pytest
from camt053.models import Balance, ParsedDocument
from camt053.schema_version import CURRENT_SCHEMA_VERSIONS

from camt053_loader_mt942 import __version__, parse_mt942


def _minimal_mt942() -> str:
    """Return a full valid MT942 payload covering every supported tag."""
    return (
        ":20:INTRA-1\n"
        ":25:COBADEFFXXX/DE89370400440532013000\n"
        ":28C:42/1\n"
        ":34F:EURD1000,00\n"
        ":34F:EURC500,00\n"
        ":13D:2606211430+0200\n"
        ":61:2606210621CR500,00NMSCREF1//CREF1\n"
        ":86:Customer payment\n"
        ":61:2606210621D200,00NMSCREF2//CREF2\n"
        ":86:Card settlement\n"
        ":90D:1EUR200,00\n"
        ":90C:1EUR500,00\n"
    )


# ─── Package metadata ────────────────────────────────────────────────────────


def test_version_exposed() -> None:
    """The package exposes a non-empty semantic-style version string."""
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2


# ─── Message type / camt.052 correctness proof ───────────────────────────────


def test_minimum_payload_parses_to_camt052_document() -> None:
    """A minimal MT942 produces a camt.052 ParsedDocument, one report."""
    doc = parse_mt942(_minimal_mt942())
    assert isinstance(doc, ParsedDocument)
    assert doc.message_type == "camt.052.001.08"
    assert doc.msg_id == "INTRA-1"
    assert len(doc.statements) == 1


def test_message_type_is_a_camt053_recognised_camt052_version() -> None:
    """The output message type is a camt.052 version camt053 recognises.

    This is the correctness proof that the document is a valid camt.052
    report as far as the upstream camt053 model is concerned: its own
    ``CURRENT_SCHEMA_VERSIONS`` registry lists the exact type string.
    """
    doc = parse_mt942(_minimal_mt942())
    assert doc.message_type in CURRENT_SCHEMA_VERSIONS
    assert doc.message_type.startswith("camt.052.")


def test_document_round_trips_through_to_dict() -> None:
    """The document serialises via the camt053 model's to_dict() cleanly.

    Mirrors the MT940 sibling's round-trip proof: an MT942-sourced
    document is shape-compatible with a camt.052-XML-sourced one.
    """
    doc = parse_mt942(_minimal_mt942())
    payload = doc.to_dict()
    assert payload["message_type"] == "camt.052.001.08"
    assert payload["msg_id"] == "INTRA-1"
    assert payload["creation_date_time"] == "2026-06-21T14:30:00+02:00"
    assert len(payload["statements"]) == 1
    statement = payload["statements"][0]
    assert statement["account"]["iban"] == "DE89370400440532013000"
    assert len(statement["entries"]) == 2
    assert len(statement["balances"]) == 4  # 2 floor limits + 2 summaries


# ─── :25: account identification ─────────────────────────────────────────────


def test_account_parsing_with_bic_prefix() -> None:
    """:25: with BIC/account splits into servicer_bic + iban."""
    account = parse_mt942(_minimal_mt942()).statements[0].account
    assert account.servicer_bic == "COBADEFFXXX"
    assert account.iban == "DE89370400440532013000"
    assert account.other_id is None


def test_account_parsing_without_bic_prefix() -> None:
    """:25: without BIC puts the value in iban if it looks IBAN-like."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n"
    account = parse_mt942(mt942).statements[0].account
    assert account.iban == "DE89370400440532013000"
    assert account.servicer_bic is None


def test_proprietary_account_id_falls_through_to_other_id() -> None:
    """A non-IBAN account ID is stored on other_id, not iban."""
    mt942 = ":20:REF\n:25:1234567890\n:28C:1/1\n"
    account = parse_mt942(mt942).statements[0].account
    assert account.iban is None
    assert account.other_id == "1234567890"


def test_account_with_trailing_slash_only_bic() -> None:
    """A :25: like ``BIC/`` yields a BIC and a None account id."""
    mt942 = ":20:REF\n:25:COBADEFFXXX/\n:28C:1/1\n"
    account = parse_mt942(mt942).statements[0].account
    assert account.servicer_bic == "COBADEFFXXX"
    assert account.iban is None
    assert account.other_id is None


# ─── :28C: sequence number ───────────────────────────────────────────────────


def test_sequence_number_recorded_on_statement() -> None:
    """:28C: populates both id and electronic_seq_nb."""
    statement = parse_mt942(_minimal_mt942()).statements[0]
    assert statement.id == "42/1"
    assert statement.electronic_seq_nb == "42/1"


# ─── :34F: floor limits ──────────────────────────────────────────────────────


def test_floor_limits_map_to_proprietary_balances() -> None:
    """:34F: debit + credit floor limits become FLIMD / FLIMC balances."""
    balances = parse_mt942(_minimal_mt942()).statements[0].balances
    floors = [b for b in balances if b.type_code.startswith("FLIM")]
    assert len(floors) == 2
    debit, credit = floors
    assert debit.type_code == "FLIMD"
    assert debit.credit_debit_indicator == "DBIT"
    assert debit.amount == "1000.00"
    assert debit.currency == "EUR"
    assert debit.date is None
    assert credit.type_code == "FLIMC"
    assert credit.credit_debit_indicator == "CRDT"
    assert credit.amount == "500.00"


def test_floor_limit_without_dc_mark_defaults_to_debit() -> None:
    """A :34F: with no D/C mark applies to debits (FLIMD)."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:34F:EUR1000,00\n"
    floor = parse_mt942(mt942).statements[0].balances[0]
    assert floor.type_code == "FLIMD"
    assert floor.credit_debit_indicator == "DBIT"
    assert floor.amount == "1000.00"


def test_floor_limit_tolerates_space_before_amount() -> None:
    """A :34F: like ``EUR D1000,00`` (space-separated) still parses."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:34F:EUR D1000,00\n"
    floor = parse_mt942(mt942).statements[0].balances[0]
    assert floor.type_code == "FLIMD"
    assert floor.amount == "1000.00"


def test_malformed_floor_limit_raises() -> None:
    """A malformed :34F: raises ValueError mentioning the tag."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:34F:JUNK\n"
    with pytest.raises(ValueError, match="34F"):
        parse_mt942(mt942)


# ─── :90D: / :90C: entry summaries ───────────────────────────────────────────


def test_debit_credit_summaries_map_to_proprietary_balances() -> None:
    """:90D:/:90C: become SUMD/SUMC balances with count + sum."""
    balances = parse_mt942(_minimal_mt942()).statements[0].balances
    summaries = [b for b in balances if b.type_code.startswith("SUM")]
    assert len(summaries) == 2
    debit, credit = summaries
    assert debit.type_code == "SUMD:1"
    assert debit.credit_debit_indicator == "DBIT"
    assert debit.amount == "200.00"
    assert debit.currency == "EUR"
    assert credit.type_code == "SUMC:1"
    assert credit.credit_debit_indicator == "CRDT"
    assert credit.amount == "500.00"


def test_summary_count_is_preserved() -> None:
    """The :90x: NbOfNtries count is encoded in the type_code."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:90D:12EUR3456,78\n"
    summary = parse_mt942(mt942).statements[0].balances[0]
    assert summary.type_code == "SUMD:12"
    assert summary.amount == "3456.78"


def test_malformed_summary_raises() -> None:
    """A malformed :90C: raises ValueError mentioning the tag."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:90C:GARBAGE\n"
    with pytest.raises(ValueError, match="90C"):
        parse_mt942(mt942)


# ─── :13D: date/time indication ──────────────────────────────────────────────


def test_datetime_indication_maps_to_creation_date_time() -> None:
    """:13D: becomes an ISO-8601 creation_date_time on doc + statement."""
    doc = parse_mt942(_minimal_mt942())
    assert doc.creation_date_time == "2026-06-21T14:30:00+02:00"
    assert doc.statements[0].creation_date_time == "2026-06-21T14:30:00+02:00"


def test_negative_utc_offset_in_datetime_indication() -> None:
    """A :13D: with a negative UTC offset keeps the sign."""
    mt942 = (
        ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:13D:2606210930-0500\n"
    )
    assert parse_mt942(mt942).creation_date_time == "2026-06-21T09:30:00-05:00"


def test_malformed_datetime_indication_yields_none() -> None:
    """A malformed :13D: leaves creation_date_time None (no crash)."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:13D:NONSENSE\n"
    assert parse_mt942(mt942).creation_date_time is None


def test_absent_datetime_indication_leaves_creation_none() -> None:
    """With no :13D:, creation_date_time stays None."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n"
    assert parse_mt942(mt942).creation_date_time is None


# ─── :61: statement lines ────────────────────────────────────────────────────


def test_entries_carry_amount_dc_and_dates() -> None:
    """Each :61: line becomes an Entry with parsed amount and dates."""
    entries = parse_mt942(_minimal_mt942()).statements[0].entries
    assert len(entries) == 2
    assert entries[0].amount == "500.00"
    assert entries[0].credit_debit_indicator == "CRDT"
    assert entries[0].value_date == "2026-06-21"
    assert entries[0].booking_date == "2026-06-21"
    assert entries[0].reference == "REF1"
    assert entries[0].account_servicer_ref == "CREF1"
    assert entries[0].status == "BOOK"
    assert entries[1].credit_debit_indicator == "DBIT"
    assert entries[1].amount == "200.00"


def test_reversal_indicators_rd_rc_set_flag() -> None:
    """Debit/credit codes RD and RC set reversal_indicator=True."""
    mt942 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":61:2606210621RD100,00NMSCREVD//CR-D\n"
        ":61:2606210621RC50,00NMSCREVC//CR-C\n"
    )
    entries = parse_mt942(mt942).statements[0].entries
    assert [e.reversal_indicator for e in entries] == [True, True]
    assert [e.credit_debit_indicator for e in entries] == ["DBIT", "CRDT"]


def test_entry_without_booking_date_only_carries_value_date() -> None:
    """A :61: line with no MMDD booking date leaves booking_date None."""
    mt942 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":61:260621CR100,00NMSCREF//CR\n"
    )
    entry = parse_mt942(mt942).statements[0].entries[0]
    assert entry.value_date == "2026-06-21"
    assert entry.booking_date is None


def test_entry_without_customer_ref_leaves_servicer_ref_none() -> None:
    """A :61: line without `//CustomerRef` leaves account_servicer_ref None."""
    mt942 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":61:2606210621CR100,00NMSCREF\n"
    )
    entry = parse_mt942(mt942).statements[0].entries[0]
    assert entry.reference == "REF"
    assert entry.account_servicer_ref is None


def test_malformed_statement_line_raises() -> None:
    """A :61: line that doesn't match the grammar raises ValueError."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:61:GARBAGE\n"
    with pytest.raises(ValueError, match=":61:"):
        parse_mt942(mt942)


# ─── :86: information to account owner ───────────────────────────────────────


def test_tag_86_attaches_as_additional_info_on_last_entry() -> None:
    """:86: attaches to the most recent :61: as a TransactionDetails row."""
    first_entry = parse_mt942(_minimal_mt942()).statements[0].entries[0]
    assert len(first_entry.details) == 1
    assert first_entry.details[0].additional_info == "Customer payment"


def test_orphan_tag_86_without_preceding_entry_is_ignored() -> None:
    """:86: before any :61: is silently ignored (Postel's law)."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n:28C:1/1\n:86:Orphan info\n"
    doc = parse_mt942(mt942)
    assert doc.statements[0].entries == []


# ─── Unknown / mandatory fields ──────────────────────────────────────────────


def test_unknown_tags_are_ignored() -> None:
    """Unknown :tag: values don't break parsing."""
    mt942 = (
        ":20:REF\n"
        ":21:RELATED-REF\n"  # related reference, unsupported
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
    )
    assert parse_mt942(mt942).msg_id == "REF"


def test_missing_tag_20_raises() -> None:
    """A payload without :20: raises ValueError with a clear message."""
    mt942 = ":25:DE89370400440532013000\n:28C:1/1\n"
    with pytest.raises(ValueError, match=":20:"):
        parse_mt942(mt942)


def test_empty_reference_on_tag_20_raises() -> None:
    """A :20: with empty value still raises (msg_id is required)."""
    mt942 = ":20:\n:25:DE89370400440532013000\n:28C:1/1\n"
    with pytest.raises(ValueError, match=":20:"):
        parse_mt942(mt942)


def test_missing_tag_25_raises() -> None:
    """A payload without :25: raises ValueError naming the account tag."""
    mt942 = ":20:REF\n:28C:1/1\n"
    with pytest.raises(ValueError, match=":25:"):
        parse_mt942(mt942)


def test_missing_tag_28c_raises() -> None:
    """A payload without :28C: raises ValueError naming the sequence tag."""
    mt942 = ":20:REF\n:25:DE89370400440532013000\n"
    with pytest.raises(ValueError, match=":28C:"):
        parse_mt942(mt942)


# ─── Date handling ───────────────────────────────────────────────────────────


def test_19xx_year_window_for_old_dates() -> None:
    """YY ≥ 80 maps to 19YY (sliding-window convention)."""
    mt942 = (
        ":20:REF\n"
        ":25:DE89370400440532013000\n"
        ":28C:1/1\n"
        ":61:950620CR100,00NMSCREF\n"
    )
    entry = parse_mt942(mt942).statements[0].entries[0]
    assert entry.value_date == "1995-06-20"


def test_balances_list_holds_only_proprietary_interim_codes() -> None:
    """Every balance an MT942 produces is a documented proprietary code.

    Guards the model-limitation contract: an interim report carries no
    OPBD/CLBD booked balances, only floor limits and summaries.
    """
    statement = parse_mt942(_minimal_mt942()).statements[0]
    balances: list[Balance] = statement.balances
    for balance in balances:
        assert balance.type_code.startswith(("FLIM", "SUM"))
