"""Regenerate menus_sample.csv, sales_sample.csv, market_type_sample.json and
request_sample.json from the sample client's miniature market.

    python make_samples.py

The CSVs are the two input tables exactly as you would keep them in a
spreadsheet; request_sample.json is the ready-to-send POST /fit body they
combine into (tables as JSON records).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "client"))

from example_client import MARKET_TYPE, build_sheets  # noqa: E402
from wire import records  # noqa: E402


def main() -> None:
    menus, sales = build_sheets()
    menus.to_csv(os.path.join(HERE, "menus_sample.csv"), index=False)
    sales.to_csv(os.path.join(HERE, "sales_sample.csv"), index=False)
    with open(os.path.join(HERE, "market_type_sample.json"), "w") as f:
        json.dump(MARKET_TYPE, f, indent=2)
    with open(os.path.join(HERE, "request_sample.json"), "w") as f:
        json.dump(
            {"menus": records(menus), "sales": records(sales), "market_type": MARKET_TYPE},
            f, indent=1,
        )
    print(f"wrote {len(menus)} menu rows, {len(sales)} sales rows")


if __name__ == "__main__":
    main()
