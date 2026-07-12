# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Minimal example: parse a tiny MT942 payload and inspect the result.

Run with ``python examples/01_minimal_parse.py``.
"""

from camt053_loader_mt942 import parse_mt942

MT942 = """:20:INTRA-DEMO-1
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


def main() -> None:
    """Parse the demo MT942 and print a one-line summary."""
    document = parse_mt942(MT942)
    statement = document.statements[0]
    print(f"msg_id        : {document.msg_id}")
    print(f"message_type  : {document.message_type}")
    print(f"report time   : {document.creation_date_time}")
    print(f"account IBAN  : {statement.account.iban}")
    print(f"servicer BIC  : {statement.account.servicer_bic}")
    print(f"entries       : {len(statement.entries)}")
    for entry in statement.entries:
        info = (
            entry.details[0].additional_info if entry.details else "(no info)"
        )
        print(
            f"  {entry.credit_debit_indicator} "
            f"{entry.amount} ref={entry.reference} :86:={info!r}"
        )
    print("floor limits / summaries (proprietary type codes):")
    for balance in statement.balances:
        print(
            f"  {balance.type_code:<10} "
            f"{balance.credit_debit_indicator} "
            f"{balance.amount} {balance.currency}"
        )


if __name__ == "__main__":
    main()
