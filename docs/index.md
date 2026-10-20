<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# camt053-loader-mt942 user manual

`camt053-loader-mt942` reads a SWIFT MT942 interim transaction report and
returns a `camt053.models.ParsedDocument` tagged as an ISO 20022 camt.052
account report.

- [Install and Quick Start](../README.md#install): `pip install
  camt053-loader-mt942`, then `parse_mt942(text)`.
- [Tag mapping](../README.md#features): which MT942 field fills which model
  field, the proprietary balance codes, and the model's limitations.
- [Errors](../README.md#quick-start): a missing `:20:`, `:25:` or `:28C:`,
  or a malformed `:34F:`, `:61:` or `:90x:`, raises `ValueError` naming the
  field. A malformed `:13D:` yields no timestamp rather than an error.
- [Comparison with the suite's other readers](COMPARISON.md).
- [Benchmarks](BENCHMARKS.md): methodology and results.
- [Toolchain policy](POLICIES.md): the Python floor and how it moves.
- [Security policy](../SECURITY.md) and [contributing](../CONTRIBUTING.md).

The API reference is the docstring of `parse_mt942` in
[`camt053_loader_mt942/loader.py`](../camt053_loader_mt942/loader.py)
(`python -c "import camt053_loader_mt942; help(camt053_loader_mt942.parse_mt942)"`).
