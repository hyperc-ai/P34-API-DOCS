"""Demo: P34 vs an industry-standard boosting profit regressor.

The point of this demo is the failure mode P34 is designed to avoid. Your
history is BIASED: you only observed profits for the options your business
actually took, and it took them selectively. A regressor trained on that
history looks great on business-observed holdouts — and then over-trades
false positives on the full future menu.

What the script does:

1. Generates a synthetic market with KNOWN ground truth (per-key latent demand;
   only some keys are genuinely profitable). Ground truth stays local — it is
   never sent to the API (the API would refuse it on task rows anyway).
2. Builds the documented Menus/Sales sheets from it: 12 historical weeks in
   which a plausible-but-imperfect business chose one option per key, and a
   T=0 task menu.
3. Baseline: trains a gradient-boosting regressor (features+qty -> profit) on
   the labeled historical rows only; per key takes the best positive-predicted
   qty (the arena's "boosting-gbdt" baseline logic).
4. P34: submits the same sheets to the API and polls for the portfolio.
5. Scores BOTH portfolios against the simulator's true future demand and
   prints a side-by-side comparison.

Run offline (baseline only, no key needed):

    python demo_regressor.py --offline

Full comparison (a real cluster fit; takes minutes):

    export P34_API_KEY=...          # https://api.hyperc.com/app/
    python demo_regressor.py

Requires: pandas numpy scikit-learn requests pyarrow
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client"))
from wire import records  # noqa: E402

HOLD_WEEKS = 8          # write-off horizon
HOLD_COST = 0.15        # per unit per market: holding cost baked into unit economics
QTYS = (1, 2, 4, 8)     # deal-size options on every menu

MARKET_TYPE = {
    "market_type": "synthetic_inventory",
    "parameters": {
        "qty_ordered_range": max(QTYS),
        "inventory_holding_weeks_before_writeoff": HOLD_WEEKS,
        "holding_cost_per_unit": HOLD_COST,
        "leftover_writeoff_fraction": 1.0,
        "grounding_labelling_mode": "synthetic_full",
    },
}


# ---------------------------------------------------------------------------
# 1. synthetic market with known ground truth
# ---------------------------------------------------------------------------

def make_market(n_keys: int = 120, seed: int = 3):
    """Each key has a latent weekly demand rate; features are NOISY signals of
    it. Roughly a third of keys are genuinely profitable at some size."""
    rng = np.random.default_rng(seed)
    keys = pd.DataFrame({
        "key": [f"K{k:04d}" for k in range(n_keys)],
        "demand_rate": rng.gamma(1.2, 0.9, n_keys),           # units/week, skewed
        "unit_cost": np.round(rng.uniform(5, 25, n_keys), 2),
    })
    keys["unit_price"] = np.round(keys["unit_cost"] * rng.uniform(1.05, 1.9, n_keys), 2)
    # two observable features: an informative-but-noisy demand signal and noise
    keys["f_signal"] = keys["demand_rate"] * rng.lognormal(0, 0.6, n_keys)
    keys["f_noise"] = rng.normal(0, 1, n_keys)
    return keys


def simulate_weeks(keys: pd.DataFrame, qty: np.ndarray, rng) -> np.ndarray:
    """True realized profit of ordering `qty` units of every key: Poisson sales
    against latent demand for HOLD_WEEKS, then leftovers written off."""
    sold = np.minimum(qty, rng.poisson(keys["demand_rate"].to_numpy() * HOLD_WEEKS))
    margin = (keys["unit_price"] - keys["unit_cost"]).to_numpy()
    holding = HOLD_COST * qty * (HOLD_WEEKS / 2)
    writeoff = (qty - sold) * keys["unit_cost"].to_numpy()
    return sold * margin - holding - writeoff


def build_history(keys: pd.DataFrame, weeks: int = 12, seed: int = 4):
    """Historical menus: every (key, qty) option each week; the business chose
    ONE option per key using a decent-but-imperfect heuristic, and only chosen
    rows have observed profit. Plus the matching weekly sales log."""
    rng = np.random.default_rng(seed)
    menus_rows, sales_rows = [], []
    for w in range(weeks):
        t_menu = -(weeks - w) * HOLD_WEEKS            # menus spaced a horizon apart
        menu_id = 1000 + w
        # the business's heuristic: order roughly signal*horizon, snapped to a qty
        target = keys["f_signal"].to_numpy() * HOLD_WEEKS * rng.uniform(0.5, 1.1, len(keys))
        would_take = np.array([min(QTYS, key=lambda q: abs(q - t)) for t in target])
        declined = keys["unit_price"].to_numpy() < keys["unit_cost"].to_numpy() * 1.15
        chosen = np.where(declined, 0, would_take)
        # realized outcome of the chosen size (ground truth simulation)
        profit = simulate_weeks(keys, chosen, rng)
        weekly_share = rng.dirichlet(np.ones(HOLD_WEEKS), len(keys))
        sold_total = np.minimum(chosen, rng.poisson(keys["demand_rate"].to_numpy() * HOLD_WEEKS))

        for i, row in keys.iterrows():
            f_sig = row["f_signal"] * rng.lognormal(0, 0.15)   # features drift week to week
            f_noi = rng.normal(0, 1)
            # the API requires each historical key to live on exactly ONE menu
            # (sales attribution is per key), so the same product on different
            # weeks travels under a distinct per-week key id
            week_key = f"{row['key']}#w{w}"
            for q in QTYS:
                menus_rows.append({
                    "key": week_key, "menu": menu_id, "T": t_menu, "T_lead": 0,
                    "f_signal": f_sig, "f_noise": f_noi,
                    "unit_cost": row["unit_cost"], "unit_price": row["unit_price"],
                    "qty": q, "historically_available": 1,
                    # a declined group still carries ONE flagged row: without a
                    # chosen row the group is dropped whole at intake, and P34
                    # needs the declined groups as its unlabeled context. WHICH
                    # row wears the flag is immaterial where there is no
                    # outcome — this reuses would_take because it is to hand,
                    # not because anything downstream reads the value.
                    "historically_chosen": int(q == would_take[i]),
                    "profit": float(profit[i]) if (q == chosen[i] and not declined[i]) else None,
                })
            if declined[i]:
                # "no trade" was the choice: the group stays in with profit
                # blank on every row and no sales — the unobserved context
                pass
            else:
                sold_weeks = np.round(weekly_share[i] * sold_total[i]).astype(int)
                for dw, qty_sold in enumerate(sold_weeks):
                    if qty_sold > 0 and t_menu + dw <= 0:
                        sales_rows.append({
                            "key": week_key, "menu": menu_id, "T": t_menu + dw,
                            "T_signal_delay": None, "qty": int(qty_sold),
                            "price": row["unit_price"],
                            "unit_holding_cost": HOLD_COST, "unit_fee": None,
                        })
    return pd.DataFrame(menus_rows), pd.DataFrame(sales_rows)


def build_task(keys: pd.DataFrame, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _, row in keys.iterrows():
        f_sig = row["f_signal"] * rng.lognormal(0, 0.15)
        f_noi = rng.normal(0, 1)
        for q in QTYS:
            rows.append({
                "key": row["key"], "menu": 0, "T": 0, "T_lead": 0,
                "f_signal": f_sig, "f_noise": f_noi,
                "unit_cost": row["unit_cost"], "unit_price": row["unit_price"],
                "qty": q, "historically_available": None,
                "historically_chosen": None, "profit": None,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. the baseline: GBDT profit regression on the labeled history
# ---------------------------------------------------------------------------

FEATURES = ["f_signal", "f_noise", "unit_cost", "unit_price", "qty"]


def baseline_portfolio(hist_menus: pd.DataFrame, task_menu: pd.DataFrame) -> pd.DataFrame:
    from sklearn.ensemble import HistGradientBoostingRegressor

    labeled = hist_menus[hist_menus["profit"].notna()]
    reg = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, random_state=42)
    reg.fit(labeled[FEATURES], labeled["profit"].astype(float))

    menu = task_menu.drop(columns=["profit"]).copy()   # blank task column, avoid clash
    menu["_pred"] = reg.predict(menu[FEATURES])
    best = menu.loc[menu.groupby("key")["_pred"].idxmax()]
    best = best[best["_pred"] > 0]
    return best.rename(columns={"_pred": "profit"})[["key", "qty", "profit"]]


# ---------------------------------------------------------------------------
# 3. P34 via the API
# ---------------------------------------------------------------------------

def p34_portfolio(url: str, key: str | None, model: str | None,
                  menus: pd.DataFrame, sales: pd.DataFrame,
                  poll_s: int = 30, timeout_min: int = 45) -> pd.DataFrame:
    import requests

    headers = {"Authorization": f"Bearer {key}"} if key else {}
    body = {"menus": records(menus), "sales": records(sales), "market_type": MARKET_TYPE}
    if model:
        body["model"] = model
    r = requests.post(f"{url}/fit", json=body, headers=headers, timeout=300)
    r.raise_for_status()
    out = r.json()
    print(f"  P34 fit queued — session {out['session_id'][:8]}, "
          f"{out['labeled_rows']} labeled rows")
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        res = requests.get(f"{url}/result/{out['session_id']}", headers=headers, timeout=30).json()
        if res["status"] in ("done", "failed"):
            break
        print(f"  … {res['status']}")
        time.sleep(poll_s)
    if res["status"] != "done":
        raise RuntimeError(f"P34 fit not done: {res['status']} {res.get('error', '')}")
    port = pd.DataFrame(res["menu"])
    if port.empty:            # a valid answer: the model takes no trades
        return pd.DataFrame(columns=["key", "qty", "profit"])
    return port[port["qty"] > 0][["key", "qty", "profit"]]


# ---------------------------------------------------------------------------
# 4. score both against ground truth (LOCAL ONLY)
# ---------------------------------------------------------------------------

def score(name: str, portfolio: pd.DataFrame, keys: pd.DataFrame, seed: int = 99) -> dict:
    rng = np.random.default_rng(seed)
    qty = np.zeros(len(keys))
    pos = keys.set_index("key").index.get_indexer(portfolio["key"])
    qty[pos] = portfolio["qty"].to_numpy()
    # average over many future demand draws for a stable realized-profit figure
    realized = np.mean([simulate_weeks(keys, qty, rng).sum() for _ in range(200)])
    losers = 0
    if len(portfolio):
        per_key = np.mean([simulate_weeks(keys, qty, rng) for _ in range(200)], axis=0)
        losers = int((per_key[pos] < 0).sum())
    return {
        "model": name,
        "trades": len(portfolio),
        "predicted_profit": float(portfolio["profit"].sum()) if len(portfolio) else 0.0,
        "realized_profit(sim)": round(float(realized), 1),
        "loss_making_trades": losers,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("P34_API_URL", "https://api.hyperc.com/v1"))
    ap.add_argument("--key", default=os.environ.get("P34_API_KEY"))
    ap.add_argument("--model", default=None, help="P34 model version (default: server default)")
    ap.add_argument("--offline", action="store_true", help="baseline only, no API call")
    ap.add_argument("--keys", type=int, default=120)
    args = ap.parse_args()

    keys = make_market(n_keys=args.keys)
    hist_menus, sales = build_history(keys)
    task = build_task(keys)
    menus = pd.concat([hist_menus, task], ignore_index=True)
    print(f"market: {len(keys)} keys, {hist_menus['menu'].nunique()} historical menus, "
          f"{len(sales)} sales rows, task menu {task['key'].nunique()} keys x {len(QTYS)} sizes")

    results = []

    print("\n[baseline] gradient-boosting profit regressor on labeled history …")
    base = baseline_portfolio(hist_menus, task)
    results.append(score("boosting-baseline", base, keys))

    if not args.offline:
        print("\n[P34] submitting the same sheets to the API …")
        p34 = p34_portfolio(args.url.rstrip("/"), args.key, args.model, menus, sales)
        results.append(score("P34", p34, keys))

    print("\n=== comparison (realized profit simulated from the TRUE demand, locally) ===")
    print(pd.DataFrame(results).to_string(index=False))
    if args.offline:
        print("\n(offline mode: set P34_API_KEY and re-run without --offline "
              "to add the P34 row)")
    print("\nNote the baseline's gap between predicted and realized profit and its "
          "loss-making trades: selection bias in the history rewards over-trading.")


if __name__ == "__main__":
    main()
