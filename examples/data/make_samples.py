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

from example_client import BUSINESS_DESCRIPTION, MARKET_TYPE, build_sheets  # noqa: E402
from wire import records  # noqa: E402


def main() -> None:
    # kept deliberately tiny (12 keys): these files are a FORMAT reference to
    # eyeball, not a floor-clearing payload — build_sheets' defaults (300 keys)
    # are the cluster-viable size the client and pytest examples submit
    menus, sales = build_sheets(n_keys=12)
    menus.to_csv(os.path.join(HERE, "menus_sample.csv"), index=False)
    sales.to_csv(os.path.join(HERE, "sales_sample.csv"), index=False)
    with open(os.path.join(HERE, "market_type_sample.json"), "w") as f:
        json.dump(MARKET_TYPE, f, indent=2)
    with open(os.path.join(HERE, "request_sample.json"), "w") as f:
        json.dump(
            {"menus": records(menus), "sales": records(sales), "market_type": MARKET_TYPE,
             "business_description": BUSINESS_DESCRIPTION},
            f, indent=1,
        )

    # the client_grounded shape: a profit on EVERY option row the caller valued,
    # no business_description needed (nothing is compiled from it), and the
    # plausibility checks switched off because this tiny market is under them
    cg_menus, cg_sales = build_sheets(n_keys=12, ground_all=True)
    with open(os.path.join(HERE, "request_client_grounded_sample.json"), "w") as f:
        json.dump(
            {"menus": records(cg_menus), "sales": records(cg_sales),
             "market_type": MARKET_TYPE,
             "grounding_mode": "client_grounded", "checks": "off"},
            f, indent=1,
        )
    labeled = sum(1 for r in records(cg_menus) if r.get("profit") is not None)
    print(f"wrote {len(menus)} menu rows, {len(sales)} sales rows")
    print(f"wrote client_grounded sample: {len(cg_menus)} menu rows, "
          f"{labeled} carrying a client label")


if __name__ == "__main__":
    main()
