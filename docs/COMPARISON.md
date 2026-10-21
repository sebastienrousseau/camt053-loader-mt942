<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Comparison

The camt053 suite reads interim reports, end-of-day statements and native
ISO 20022 XML into one model, `camt053.models.ParsedDocument`. This table
is taken from each package's source: `camt053_loader_mt942/loader.py`,
`camt053_loader_mt940/loader.py` and `camt053/parse/statement_parser.py`.

| | camt053-loader-mt942 | camt053-loader-mt940 | camt053 XML parser |
| :--- | :---: | :---: | :---: |
| Input | SWIFT MT942 text | SWIFT MT940 text | camt.052/053/054 XML |
| Output `message_type` | `camt.052.001.08` | `camt.053.001.08` | as in the document |
| Reference, account, sequence (`:20:`, `:25:`, `:28C:`) | yes, all mandatory | yes | from `GrpHdr` / `Stmt` |
| Booked balances | none (MT942 has none) | `:60F:/:60M:` `OPBD`, `:62F:/:62M:` `CLBD`, `:64:` `CLAV`, `:65:` `FWAV` | `<Bal>` |
| Floor limits (`:34F:`) | `FLIMD` / `FLIMC` balances | not applicable | not modelled |
| Entry summaries (`:90D:`, `:90C:`) | `SUMD:<n>` / `SUMC:<n>` balances | not applicable | not modelled |
| Report timestamp (`:13D:`) | `creation_date_time` | not applicable | `CreDtTm` |
| Reversals (`RC`, `RD`) | `reversal_indicator` | `reversal_indicator` | `RvslInd` |
| `:86:` information | `TransactionDetails.additional_info` | `TransactionDetails.additional_info` | `AddtlTxInf` |

No third-party MT942 parser has been measured against this one, so the
table makes no speed or coverage claim beyond the suite.
