# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Parse MT942 and emit JSON via the camt053 model's ``to_dict``.

This example shows that an MT942-sourced document is shape-compatible
with a camt.052-XML-sourced document: every downstream consumer in the
suite (writer, validator, MCP server, LSP server) sees the same data
structure regardless of where the bytes came from. Only the
``message_type`` marks it as a camt.052 Account Report.

Run with ``python examples/02_round_trip_to_dict.py``.
"""

import json

from camt053_loader_mt942 import parse_mt942

MT942 = """:20:INTRA-DEMO-2
:25:DE89370400440532013000
:28C:1/1
:34F:EURD500,00
:13D:2606221015+0100
:61:2606220622D250,00NMSCDIRECTDEBIT//INV-77
:86:Mietzahlung
:61:2606220622RC50,00NMSCRETURNED//RET-77
:86:Returned by debtor
:90D:1EUR250,00
:90C:1EUR50,00
"""


def main() -> None:
    """Parse the demo MT942 and dump its dict shape as JSON."""
    document = parse_mt942(MT942)
    print(json.dumps(document.to_dict(), indent=2))


if __name__ == "__main__":
    main()
