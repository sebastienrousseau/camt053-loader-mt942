<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/camt053/v1/logos/camt053.svg" alt="camt053-loader-mt942 logo" width="128" />
</p>

<h1 align="center">camt053-loader-mt942</h1>

<p align="center">
  Converts legacy SWIFT MT942 interim transaction reports into the camt053 model as ISO 20022 camt.052 account reports.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/camt053-loader-mt942/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/camt053-loader-mt942/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/camt053-loader-mt942/"><img src="https://img.shields.io/pypi/v/camt053-loader-mt942?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="docs/index.md"><img src="https://img.shields.io/badge/docs-source-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/camt053-loader-mt942"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/camt053-loader-mt942?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/camt053-loader-mt942/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10 or newer" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="camt053-loader-mt942 demo: an MT942 interim report, then examples/01_minimal_parse.py printing the camt.052 document it becomes, with its entries, floor limits and entry summaries" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install) — `pip install`, one runtime dependency
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — one call from MT942 text to a camt.052 `ParsedDocument`

**The camt053-loader-mt942 ecosystem**

- [The camt053-loader-mt942 ecosystem](#the-camt053-loader-mt942-ecosystem) — the six packages of the camt053 suite

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use camt053-loader-mt942](#when-not-to-use-camt053-loader-mt942) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
pip install camt053-loader-mt942
```

> **Latest release: v0.0.20.** SWIFT MT942 (the intraday sibling of
> MT940) is scheduled for retirement in November 2028. This loader covers
> the window where banks still produce MT942 but downstream tooling
> expects camt.052.

The package pulls in [`camt053`][core] and has no other runtime
dependency. It is pure Python and runs wherever `camt053` does.

---

## Requirements

- Python 3.10 or newer, tested in CI on 3.10, 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](docs/POLICIES.md)).
- `camt053` 0.0.20 or newer, below 1.0. The camt053 suite releases at one
  version, so install the matching `camt053` release alongside this one.

---

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

print(document.message_type)                # camt.052.001.08
print(document.msg_id)                      # INTRA-REF-1
print(document.statements[0].account.iban)  # DE89370400440532013000
print(document.creation_date_time)          # 2026-06-21T14:30:00+02:00
```

`parse_mt942` returns a `camt053.models.ParsedDocument`, the same shape the
`camt053` camt.052 XML parser produces, tagged `camt.052.001.08`. Every
consumer in the suite (the Excel writer, the validator, the MCP and LSP
servers) reads it unchanged. A malformed or incomplete report raises
`ValueError` naming the field.

---

## The camt053-loader-mt942 ecosystem

`camt053-loader-mt942` is one of six independently installable packages
built around the [`camt053`][core] ISO 20022 cash-management library. The
suite ships one version number across all six and releases them together,
core first; a scheduled job compares every member against PyPI.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`camt053`][core] | Core library, CLI and FastAPI REST API for camt.052/053/054 | You parse, validate or generate ISO 20022 statements |
| [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) | Model Context Protocol server over the core | An AI agent works with bank statements |
| [`camt053-lsp`](https://github.com/sebastienrousseau/camt053-lsp) | Language Server Protocol server | You author statement data in an editor |
| [`camt053-writer-xlsx`][writer] | Excel `.xlsx` writer for a `ParsedDocument` | You hand statements to people who use spreadsheets |
| [`camt053-loader-mt940`][mt940] | SWIFT MT940 to camt.053 loader | Your bank still sends end-of-day MT940 |
| [`camt053-loader-mt942`](#install) | SWIFT MT942 to camt.052 loader: **this package** | Your bank still sends intraday MT942 |

```mermaid
flowchart LR
    A["MT942 text"] -->|parse_mt942| B["camt053-loader-mt942"]
    B -->|ParsedDocument (camt.052)| C["camt053"]
    C -->|writer / validator / MCP / LSP| D["Downstream consumers"]
```

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Parsing | `:20:`, `:25:`, `:28C:`, `:34F:`, `:13D:`, `:61:`, `:86:`, `:90D:`, `:90C:` | Released |
| Output | `camt053.models.ParsedDocument`, `message_type="camt.052.001.08"` | Released |
| Reversals | `RC` / `RD` marks set `Entry.reversal_indicator` | Released |
| Interim data | Floor limits and entry summaries as proprietary `type_code` balances | Released; see [Features](#features) |
| Line endings | CRLF and LF parse identically | Fixed in 0.0.23 |
| `:61:` subfield 9 | Supplementary details kept as the entry's first detail | Fixed in 0.0.23 |
| Validation | Missing `:20:`, `:25:` or `:28C:` and malformed fields raise `ValueError` | Released |

---

## Ecosystem comparison

The suite reads interim and end-of-day reports through one model. What
each entry point accepts and produces, from each package's source:

| Project | Input | Output `message_type` | Booked balances | Floor limits and entry summaries |
| :--- | :---: | :---: | :---: | :---: |
| **camt053-loader-mt942** | SWIFT MT942 text | `camt.052.001.08` | none (MT942 has none) | yes, proprietary codes |
| `camt053-loader-mt940` | SWIFT MT940 text | `camt.053.001.08` | `OPBD`, `CLBD`, `CLAV`, `FWAV` | no |
| `camt053` XML parser | camt.052/053/054 XML | as in the document | as in the document | no |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

Parse time grows linearly with both entries per report and reports per
file; the growth exponent is the number to read. Measured with
`python benches/bench_parse_mt942.py` on 2026-10-20.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| One report, 1,000 entries | 6.32 ms | Apple A18 Pro, Python 3.12.15, camt053 0.0.20 |
| One report, 5,000 entries | 34.68 ms | Apple A18 Pro, Python 3.12.15, camt053 0.0.20 |
| Growth exponent, entries per report | 0.96 (linear) | Apple A18 Pro, Python 3.12.15 |
| Growth exponent, reports per file | 1.04 (linear) | Apple A18 Pro, Python 3.12.15 |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

The public API is one function, `camt053_loader_mt942.parse_mt942(text)`.
Each MT942 tag maps onto the `camt053` model:

| Tag | Meaning | Mapped to |
| :--- | :--- | :--- |
| `:20:` | Transaction reference number (**mandatory**) | `ParsedDocument.msg_id` |
| `:25:` | Account identification (**mandatory**; `BIC/account` or `account`) | `Statement.account` (IBAN or proprietary `other_id` + optional `servicer_bic`) |
| `:28C:` | Statement / sequence number (**mandatory**) | `Statement.id` + `Statement.electronic_seq_nb` |
| `:34F:` | Floor limit indicator (debit / credit) | `Balance` with `type_code="FLIMD"` / `"FLIMC"` |
| `:13D:` | Date/time indication (report timestamp) | `ParsedDocument.creation_date_time` + `Statement.creation_date_time` (ISO-8601) |
| `:61:` | Statement line (movement) | `Entry` with `amount`, `credit_debit_indicator`, `value_date`, `booking_date`, `reference`, `account_servicer_ref`; line 2 (supplementary details) as the first `TransactionDetails` |
| `:86:` | Information to account owner | `TransactionDetails.additional_info` appended to the preceding entry |
| `:90D:` | Number and sum of debit entries | `Balance` with `type_code="SUMD:<count>"`, `amount=<sum>` |
| `:90C:` | Number and sum of credit entries | `Balance` with `type_code="SUMC:<count>"`, `amount=<sum>` |

- **Reversals.** A `:61:` mark of `RD` (reversal of debit) or `RC`
  (reversal of credit) sets `Entry.reversal_indicator=True`.
- **Unknown tags are ignored**, so a future SWIFT addition does not break
  parsing.
- **Interim reports carry no booked balances.** MT942 has no `:60F:` /
  `:62F:`. It reports movements above a floor limit (`:34F:`) and the
  number and sum of debit and credit movements (`:90D:` / `:90C:`), which
  camt.052 holds in `<Lmt>` and `<TxsSummry>`.
- **Model limitations.** The `camt053` model is statement-oriented: it has
  no field for `<Lmt>`, `<TxsSummry>`, an integer entry count, or an
  entry-level `AddtlNtryInf`. Rather than invent fields or drop data, the
  loader puts floor limits and summaries on `Statement.balances` with the
  proprietary codes above (the `:90x:` count follows the colon), and
  `:61:` supplementary details on the entry's details list, ahead of any
  `:86:` text. Consumers that expect only booked balances (`OPBD`, `CLBD`)
  can filter the proprietary codes by prefix.

---

## Configuration

None. `parse_mt942` takes the payload and no options, reads no
environment variables and touches no files or network.

---

## Examples

- [`examples/01_minimal_parse.py`](examples/01_minimal_parse.py): the
  smallest valid MT942, parsed and inspected (the demo above).
- [`examples/02_round_trip_to_dict.py`](examples/02_round_trip_to_dict.py):
  MT942 in, `camt053` `to_dict()` JSON out, the same shape a camt.052 XML
  source produces.
- [`benches/bench_parse_mt942.py`](benches/bench_parse_mt942.py): parse
  throughput along the two axes that grow in production.

CI runs every example and the benchmark (`--quick`) on every change.

---

## When not to use camt053-loader-mt942

- **You already receive camt.052 XML.** Parse it with the `camt053` core;
  this loader is the bridge for MT942-only sources.
- **You need MT940** (end-of-day statements). Use
  [`camt053-loader-mt940`][mt940].
- **You need bank-specific `:86:` sub-fields** (for example `?20` / `?30`
  structures). The raw `:86:` text is preserved in
  `TransactionDetails.additional_info` for you to parse downstream.
- **Your MT942 arrives encrypted or inside a SWIFT FIN envelope.** Decrypt
  and unwrap upstream and pass the report text.
- **You need first-class camt.052 `<Lmt>` or `<TxsSummry>` fields.** The
  model carries them as proprietary balance codes (see
  [Features](#features)).

---

## Development

```bash
git clone https://github.com/sebastienrousseau/camt053-loader-mt942
cd camt053-loader-mt942
python -m venv .venv && . .venv/bin/activate
make dev      # hash-pinned toolchain from requirements/ci.txt, package editable
make check    # every CI gate
make demo     # re-render .github/demo.gif (needs vhs)
```

`make check` runs ruff (lint and format), mypy in strict mode, pytest with
a 100% line and branch coverage gate, the 100% docstring gate, the
complexity ceilings against `complexity-baseline.json`, `reuse lint`, the
version-source check, the benchmark and the examples. CI also runs the
test matrix on Python 3.10 to 3.14, `pip-audit` over the pinned
requirements, CodeQL, OpenSSF Scorecard and a daily suite-consistency check
against PyPI. There are no fuzz targets yet. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Security

The whole attack surface is the text the parser is handed. MT942 is a flat
text format with no XML envelope, so the XXE and entity-expansion surface
lives in the `camt053` core (defusedxml and its XML guard), not here. Field
regexes are anchored, and parse time is linear in input size (see
[Benchmarks](#benchmarks)). A malformed report raises `ValueError` rather
than returning partial data. Releases are built by a hash-pinned toolchain
from a signed tag and published with PyPI trusted publishing and SLSA build
provenance.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](docs/index.md) · [API reference: `parse_mt942`](#features) ·
[Developer guide](CONTRIBUTING.md) · [Family map](#the-camt053-loader-mt942-ecosystem) ·
[Benchmarks](docs/BENCHMARKS.md) · [Toolchain policy](docs/POLICIES.md) ·
[Changelog](CHANGELOG.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in lockstep
with the camt053 suite. The breaking axis is the document `parse_mt942`
returns: which fields a tag fills, the proprietary `type_code` values, the
`message_type`, and which inputs raise. A change to any of these is
breaking even when the function signature does not move, and is called out
in the [changelog](CHANGELOG.md); 0.0.23 changes where `:61:`
supplementary details land. The Python floor moves only as described in the
[toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Dependencies keep their own licences.

[core]: https://github.com/sebastienrousseau/camt053
[mt940]: https://github.com/sebastienrousseau/camt053-loader-mt940
[writer]: https://github.com/sebastienrousseau/camt053-writer-xlsx
