"""Complete sample client for the P34 API.

    export P34_API_KEY=...        # from https://api.hyperc.com/app/
    python example_client.py --url https://api.hyperc.com/v1

Builds a small Menus/Sales payload in the documented format
(T < 0 history, T = 0 current menu — see docs/03-data-format.md and
examples/data/menu_api_sample.xlsx), submits it with POST /fit, sanity-checks
the payload with POST /predict, and polls GET /result until the cluster
calculation lands, then prints the returned portfolio.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wire import b64_to_df, records  # noqa: E402

MARKET_TYPE = {
    "market_type": "synthetic_inventory",
    "parameters": {
        "qty_ordered_range": 4,
        "inventory_holding_weeks_before_writeoff": 8,
        "holding_cost_per_unit": 0.1,
        "leftover_writeoff_fraction": 1.0,
        "grounding_labelling_mode": "synthetic_full",
    },
}

# Every fit must resolve to a business description: this field, or the one
# saved in the console's Business profile, or the one last sent by the
# account (422 otherwise). Describe the business AND how its unit economics
# is computed — fees, accumulated costs, holding costs; approximations OK.
# See docs/02-endpoints.md#business-description.
BUSINESS_DESCRIPTION = (
    "Synthetic inventory reseller (demo): buys SKU lots at weekly decision "
    "moments, sells over an 8-week horizon. Unit economics: net profit = "
    "unit_price - unit_cost - 0.1/unit/week holding cost; unsold leftovers "
    "are written off in full after 8 weeks; no marketplace or referral fees "
    "in this toy market."
)


def build_sheets(n_keys: int = 300, qtys: int = 3, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Menus + Sales sheets: 12 historical weekly menus (T=-12..-1) and a T=0 menu.

    Sized to the model's data floors (see docs/03-data-format.md): roughly a
    fifth of the keys are deals the desk DECLINED — their menu groups stay in
    with the would-be size flagged historically_chosen and profit blank,
    becoming the unlabeled context current models require; the observed side
    needs at least ~100 groups sharing a qty option; the history must span
    enough decision moments (12 menus here, not 2); and each menu needs a
    healthy count of observed deals (hence 300 keys ≈ 20 observed per menu).
    """
    rng = np.random.default_rng(seed)
    menus_rows, sales_rows = [], []
    for k in range(n_keys):
        key = f"A{k:03d}"                       # string keys, like the sample sheet
        t_menu = -12 + (k % 12)          # spread keys over 12 weekly menus
        cost = round(rng.uniform(8, 20), 2)
        price = round(cost * rng.uniform(1.2, 2.2), 2)
        # f_edge is a real (noisy) demand signal: high-edge deals sell,
        # low-edge deals rot on the shelf — something for the model to learn
        edge = rng.normal(0, 1)
        weekly_sales = rng.poisson(np.clip(1.0 + 0.9 * edge, 0.05, None), size=2)
        # the desk's biased selection: it passes on low-edge deals and sizes
        # its orders roughly by the same signal it screens with
        declined = bool(edge + rng.normal(0, 0.5) < -0.8)
        chosen_qty = int(np.clip(round(1.5 + edge), 1, qtys))  # taken — or would-be — size
        stock_left, sold_weeks = chosen_qty, []
        for demand in weekly_sales:              # can't sell more than was stocked
            sold = int(min(demand, stock_left))
            sold_weeks.append(sold)
            stock_left -= sold
        profit_chosen = float(sum(sold_weeks) * (price - cost) - chosen_qty * cost * 0.1)

        for q in range(1, qtys + 1):
            menus_rows.append({
                "key": key, "menu": 100 + abs(t_menu), "T": t_menu, "T_lead": 0,
                "f_edge": edge, "unit_cost": cost, "unit_price": price, "qty": q,
                "historically_available": 1,
                "historically_chosen": int(q == chosen_qty),
                "profit": profit_chosen if (q == chosen_qty and not declined) else None,
            })
            menus_rows.append({
                "key": key, "menu": 0, "T": 0, "T_lead": 0,
                "f_edge": edge + rng.normal(0, 0.1), "unit_cost": cost, "unit_price": price,
                "qty": q, "historically_available": None, "historically_chosen": None,
                "profit": None,                  # task rows NEVER carry outcomes
            })
        if declined:
            continue                            # no outcome, no sales — unlabeled context
        for week, qty_sold in enumerate(sold_weeks):
            sales_rows.append({
                "key": key, "menu": 100 + abs(t_menu), "T": t_menu + week,
                "T_signal_delay": None, "qty": qty_sold, "price": price,
                "unit_holding_cost": 0.1, "unit_fee": None,
            })
    return pd.DataFrame(menus_rows), pd.DataFrame(sales_rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("P34_API_URL", "https://api.hyperc.com/v1"))
    ap.add_argument("--key", default=os.environ.get("P34_API_KEY"))
    ap.add_argument("--model", default=None, help="model version (see GET /); default: server default")
    ap.add_argument("--confidence-correction", type=float, default=None,
                    help="signed adjustment in [-1,1] added to the model's "
                         "calibrated confidence threshold (r006+); positive = "
                         "fewer, higher-confidence selections (default: "
                         "service default -0.1)")
    ap.add_argument("--poll", type=int, default=30, help="seconds between /result polls")
    ap.add_argument("--timeout-min", type=int, default=30, help="give up after this many minutes")
    args = ap.parse_args()
    url = args.url.rstrip("/")
    headers = {"Authorization": f"Bearer {args.key}"} if args.key else {}

    info = requests.get(f"{url}/", headers=headers, timeout=10).json()
    print("service:", info.get("service"), "| models:", info.get("models"))

    menus, sales = build_sheets()
    body = {"menus": records(menus), "sales": records(sales), "market_type": MARKET_TYPE,
            "business_description": BUSINESS_DESCRIPTION}
    if args.model:
        body["model"] = args.model
    if args.confidence_correction is not None:
        body["confidence_correction"] = args.confidence_correction
    r = requests.post(f"{url}/fit", json=body, headers=headers, timeout=120)
    r.raise_for_status()
    out = r.json()
    print(f"fit ok — session {out['session_id'][:8]} ({out['status']}, model {out.get('model', 'default')})")
    print(f"  grounded: {out['labeled_rows']} labeled / {out['unlabeled_rows']} unlabeled rows")
    print(f"  report:   {out['parse_report']}")

    # instant sanity check from the in-process reference model (NOT P34's answer)
    now_menu = menus[menus["T"] == 0]
    r = requests.post(
        f"{url}/predict",
        json={"session_id": out["session_id"], "menus": records(now_menu), "market_type": MARKET_TYPE},
        headers=headers, timeout=120,
    )
    r.raise_for_status()
    selection = b64_to_df(r.json()["selection"])
    print(f"payload sanity-check ok — reference model selected {len(selection)} deals")

    # the real predictions come from the cluster — poll /result until done
    deadline = time.time() + args.timeout_min * 60
    while True:
        res = requests.get(f"{url}/result/{out['session_id']}", headers=headers, timeout=30).json()
        if res["status"] in ("done", "failed"):
            break
        if time.time() > deadline:
            print(f"still {res['status']} after {args.timeout_min} min — check the console, "
                  "or re-poll GET /result later; the session keeps computing.")
            return
        print(f"  {res['status']} … (next poll in {args.poll}s)")
        time.sleep(args.poll)

    if res["status"] == "failed":
        print("FAILED:", res.get("error"))
        return
    portfolio = pd.DataFrame(res["menu"])
    trades = portfolio[portfolio["qty"] > 0] if len(portfolio) else portfolio
    print(f"done — {len(portfolio)} keys predicted, {len(trades)} trades recommended, "
          f"predicted profit {res['predicted_profit_sum']:.2f}")
    if len(trades):
        print(trades.to_string(index=False))
    else:
        # an empty (or all-qty-0) menu is a valid answer: the model judged
        # that no deal on this menu is worth taking
        print("the model recommends taking no trades on this menu")


if __name__ == "__main__":
    main()
