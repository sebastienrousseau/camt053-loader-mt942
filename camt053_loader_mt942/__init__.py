# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""MT942 → camt.052 loader for the camt053 suite.

SWIFT MT942 is the legacy *Interim Transaction Report* — the intraday
sibling of the MT940 end-of-day statement — that banks have shipped
for decades and that ISO 20022 camt.052 (Bank-to-Customer Account
Report) replaces. Like MT940, MT942 is scheduled for retirement in
November 2028, leaving a window where SMEs, ERPs, and treasury
middleware still produce MT942 but downstream tooling expects camt.052.

This package bridges that gap: pass an MT942 text payload and get back
a :class:`camt053.models.ParsedDocument` with the same shape as
:func:`camt053.parse.statement_parser.parse_document`, tagged as a
``camt.052.001.08`` report. Downstream camt053 consumers (the writer,
validator, MCP and LSP servers) then work without further changes.
"""

from camt053_loader_mt942.loader import parse_mt942

__version__ = "0.0.1"

__all__ = ["parse_mt942", "__version__"]
