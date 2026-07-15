# camt053-loader-mt942: MT942 → camt.052 loader

<p align="center">
  <img src="https://cloudcdn.pro/camt053/v1/logos/camt053.svg" alt="camt053-loader-mt942 logo" width="128" />
</p>

[![PyPI Version][pypi-badge]][07]
[![Python Versions][python-versions-badge]][07]
[![License][license-badge]][01]
[![Tests][tests-badge]][tests-url]
[![Quality][quality-badge]][quality-url]

**Convert legacy SWIFT MT942 interim transaction reports into the same
[`camt053`][core] data model as native camt.052 input.** A single
`parse_mt942(text)` call returns a `camt053.models.ParsedDocument`
tagged as a **camt.052** Bank-to-Customer Account Report, ready for
every downstream consumer in the suite (writer, validator, MCP and LSP
servers).

> **Latest release: v0.0.13.** SWIFT MT942 (the intraday sibling of
> MT940) is scheduled for retirement in **November 2028**. This loader
> bridges the window where banks still produce MT942 but downstream
> tooling expects camt.052.

## Contents

- [Overview](#overview)
- [Install](#install)
- [Quick Start](#quick-start)
- [Supported Fields](#supported-fields)
- [Interim reports vs statements](#interim-reports-vs-statements)
- [Model limitations](#model-limitations)
- [Examples](#examples)
- [The camt053 suite](#the-camt053-suite)
- [When not to use camt053-loader-mt942](#when-not-to-use-camt053-loader-mt942)
- [Development](#development)
- [Security](#security)
- [License](#license)

## Overview

`camt053-loader-mt942` is a small, focused companion to the
[`camt053`][core] ISO 20022 cash-management library. It does one thing
well: parse the common-denominator MT942 *Interim Transaction Report*
grammar shipped by EU and UK commercial banks, and hand back the same
`ParsedDocument` shape that the camt.052 XML parser produces — only the
`message_type` differs (`camt.052.001.08`). The rest of the suite then
works unchanged.

MT942 is the **intraday** sibling of MT940. Where MT940 → camt.053
(end-of-day *Statement*), MT942 → **camt.052** (*Account Report*).
The `camt053` typed model is message-type-agnostic — its `Statement`
dataclass doubles as a camt.052 `<Rpt>` container — so MT942 lands in
the exact same `ParsedDocument` structure.

## Install

`camt053-loader-mt942` runs on macOS, Linux, and Windows and requires
**Python 3.10+** and **pip**. It pulls in `camt053` automatically and
has no other runtime dependencies.

```bash
pip install camt053-loader-mt942
```

## Quick Start

```python
from camt053_loader_mt942 import parse_mt942

mt942 = """:20:INTRA-REF-1
:25:COBADEFFXXX/DE89370400440532013000
:28C:42/1
:34F:EURD1000,00
:34F:EURC500,00
:13D:2606211430+0200
:61:2606210621CR500,00NMSCREF1//CREF1
:86:Customer payment for invoice 123
:61:2606210621D200,00NMSCREF2//CREF2
:86:Card settlement
:90D:1EUR200,00
:90C:1EUR500,00
"""

document = parse_mt942(mt942)

print(document.message_type)
# camt.052.001.08
print(document.msg_id)
# INTRA-REF-1
print(document.statements[0].account.iban)
# DE89370400440532013000
print(document.creation_date_time)
# 2026-06-21T14:30:00+02:00
```

That's a `camt053.models.ParsedDocument`, ready to feed to
[`camt053-writer-xlsx`][writer] (Excel output), the camt053 REST API,
or any other consumer in the suite.

## Supported Fields

| Tag | Meaning | Mapped to |
| :--- | :--- | :--- |
| `:20:` | Transaction reference number (**mandatory**) | `ParsedDocument.msg_id` |
| `:25:` | Account identification (**mandatory**; `BIC/account` or `account`) | `Statement.account` (IBAN or proprietary `other_id` + optional `servicer_bic`) |
| `:28C:` | Statement / sequence number (**mandatory**) | `Statement.id` + `Statement.electronic_seq_nb` |
| `:34F:` | Floor limit indicator (debit / credit) | `Balance` with `type_code="FLIMD"` / `"FLIMC"` |
| `:13D:` | Date/time indication (report timestamp) | `ParsedDocument.creation_date_time` + `Statement.creation_date_time` (ISO-8601) |
| `:61:` | Statement line (movement) | `Entry` with `amount`, `credit_debit_indicator`, `value_date`, `booking_date`, `reference`, `account_servicer_ref` |
| `:86:` | Information to account owner | `TransactionDetails.additional_info` attached to the preceding entry |
| `:90D:` | Number and sum of debit entries | `Balance` with `type_code="SUMD:<count>"`, `amount=<sum>` |
| `:90C:` | Number and sum of credit entries | `Balance` with `type_code="SUMC:<count>"`, `amount=<sum>` |

### Reversal detection

A `:61:` line whose debit/credit indicator is **`RD`** (reversal of
debit) or **`RC`** (reversal of credit) becomes an `Entry` with
`reversal_indicator=True`.

### Unknown fields

Unrecognised tags are **silently ignored**, so future SWIFT additions
do not break parsing. This follows Postel's law: be liberal in what
you accept.

## Interim reports vs statements

MT942 differs from MT940 in exactly the ways an *interim report*
differs from an *end-of-day statement*:

- **No booked opening/closing balances.** MT942 has no `:60F:` /
  `:62F:`. It reports movements *above a floor limit* (`:34F:`) rather
  than reconciling opening → closing.
- **Floor limits (`:34F:`).** The threshold above which movements are
  reported. MT942 carries a debit floor limit and, optionally, a
  separate credit floor limit.
- **Entry-count summaries (`:90D:` / `:90C:`).** The *number* and
  *sum* of debit / credit movements — camt.052's `<TxsSummry>`.

## Model limitations

The `camt053` typed model is **camt.053-statement-oriented**: it models
`<Bal>` balances but has no dedicated field for camt.052's `<Lmt>`
floor-limit block or its `<TxsSummry>` transaction-summary block, and
no integer entry-count field. Rather than invent fields or silently
drop data, this loader surfaces both on the `Statement.balances` list
using **clearly proprietary `type_code` values**:

- `:34F:` → `Balance(type_code="FLIMD" | "FLIMC")` — floor limit,
  debit / credit variant.
- `:90D:` → `Balance(type_code="SUMD:<count>", amount=<sum>)`
- `:90C:` → `Balance(type_code="SUMC:<count>", amount=<sum>)`

The `:90x:` **sum** is carried in `Balance.amount`; the ISO
`NbOfNtries` **count** is encoded into `type_code` after the colon
because the typed model has no integer count field. Downstream
consumers that only expect real balances (`OPBD` / `CLBD` / …) can
filter these proprietary codes out by prefix. If the upstream
`camt053` model later grows first-class floor-limit / transaction-
summary fields, this loader will migrate to them.

## Examples

Two runnable examples live in `examples/`:

- [`01_minimal_parse.py`](examples/01_minimal_parse.py) — the smallest
  valid MT942 + parse + inspect.
- [`02_round_trip_to_dict.py`](examples/02_round_trip_to_dict.py) —
  MT942 in, `camt053` `to_dict()` JSON out (shape-compatible with a
  camt.052-XML-sourced document).

Both are exercised in CI on every commit.

## The camt053 suite

`camt053-loader-mt942` is part of a set of independently installable
packages built around the [`camt053`][core] library:

| Package | Role |
| :--- | :--- |
| [`camt053`](https://pypi.org/project/camt053/) | Core library + CLI + FastAPI REST API |
| [`camt053-mcp`](https://pypi.org/project/camt053-mcp/) | Model Context Protocol server (for AI agents) |
| [`camt053-lsp`](https://pypi.org/project/camt053-lsp/) | Language Server Protocol server (for editors) |
| [`camt053-writer-xlsx`](https://pypi.org/project/camt053-writer-xlsx/) | Excel `.xlsx` writer for parsed statements |
| [`camt053-loader-mt940`](https://pypi.org/project/camt053-loader-mt940/) | SWIFT MT940 → camt.053 loader |
| [`camt053-loader-mt942`](https://pypi.org/project/camt053-loader-mt942/) | **SWIFT MT942 → camt.052 loader (this package)** |

```mermaid
flowchart LR
    A["MT942 text"] -->|parse_mt942| B["camt053-loader-mt942"]
    B -->|ParsedDocument (camt.052)| C["camt053"]
    C -->|writer / validator / MCP / LSP| D["Downstream consumers"]
```

## When not to use camt053-loader-mt942

- **You already have native camt.052 input.** Use the camt053 core
  parser directly — this loader is the bridge for legacy MT942-only
  data sources.
- **You need MT940** (end-of-day statement). Use
  [`camt053-loader-mt940`][mt940] instead.
- **You need bank-specific `:86:` sub-field parsing.** The raw `:86:`
  value is preserved verbatim in `TransactionDetails.additional_info`.
- **Your MT942 is PGP / GPG encrypted.** Decrypt upstream and pass the
  plaintext to the loader.

## Development

```bash
git clone https://github.com/sebastienrousseau/camt053-loader-mt942
cd camt053-loader-mt942
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                            # 100% line + branch coverage gate
interrogate camt053_loader_mt942  # 100% docstring gate
mypy camt053_loader_mt942         # strict
```

## Security

`camt053-loader-mt942` parses a flat text format with no XML envelope
— the XXE / billion-laughs surface lives upstream in the `camt053`
core (defusedxml + xml_guard). Field regexes are anchored and bounded,
so catastrophic backtracking is not a concern.

## License

Licensed under the [Apache License, Version 2.0][01]. Any contribution
submitted for inclusion shall be licensed as above, without additional
terms.

## Acknowledgements

Built on the [`camt053`][core] ISO 20022 Bank Statement library. The
MT942 grammar follows the SWIFT User Handbook MT942 specification and
the common-denominator subset shipped by major EU and UK commercial
banks.

[01]: https://opensource.org/license/apache-2-0/
[07]: https://pypi.org/project/camt053-loader-mt942/
[core]: https://github.com/sebastienrousseau/camt053
[mt940]: https://github.com/sebastienrousseau/camt053-loader-mt940
[writer]: https://github.com/sebastienrousseau/camt053-writer-xlsx
[pypi-badge]: https://img.shields.io/pypi/v/camt053-loader-mt942.svg?style=for-the-badge
[python-versions-badge]: https://img.shields.io/pypi/pyversions/camt053-loader-mt942.svg?style=for-the-badge
[license-badge]: https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge
[tests-badge]: https://img.shields.io/github/actions/workflow/status/sebastienrousseau/camt053-loader-mt942/ci.yml?branch=main&label=Tests&style=for-the-badge
[tests-url]: https://github.com/sebastienrousseau/camt053-loader-mt942/actions/workflows/ci.yml
[quality-badge]: https://img.shields.io/badge/Coverage-100%25-brightgreen?style=for-the-badge
[quality-url]: https://github.com/sebastienrousseau/camt053-loader-mt942/actions/workflows/ci.yml
