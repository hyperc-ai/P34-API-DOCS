# P34 vs a boosting-regressor baseline

A runnable demonstration of *why* the menu/sales structure matters, patterned
after HyperC's PARML-Arena benchmark: the same synthetic market is decided by

- **boosting-baseline** — the industry default: a gradient-boosting regressor
  trained `features (incl. qty) → profit` on the *labeled* historical rows,
  trading the best positive-predicted size per key. It ignores the menu
  structure, the sales log, availability and choice signals.
- **P34** — the same Menus + Sales sheets submitted to the real API.

Both portfolios are then scored against the simulator's **true demand** —
which only exists locally. Ground truth is never sent to the API (task rows
carrying outcomes are rejected with 422; see the pytest workflow).

## Run

```bash
pip install pandas numpy scikit-learn requests pyarrow

# baseline only — instant, no account needed
python demo_regressor.py --offline

# full comparison — needs an API key (https://api.hyperc.com/app/);
# the P34 fit runs on the compute cluster and takes minutes
export P34_API_KEY=...
python demo_regressor.py
python demo_regressor.py --model r003-alpha   # pick a specific model version
```

## What to look at

The final table:

| column | meaning |
| --- | --- |
| `trades` | how many keys the model chose to trade |
| `predicted_profit` | what the model *claims* the portfolio earns |
| `realized_profit(sim)` | what it *actually* earns against true demand (mean of 200 future draws) |
| `loss_making_trades` | trades whose expected true profit is negative |

The baseline's history is selectively labeled — profits exist only for options
a reasonable business chose — so its regressor systematically overestimates
the unchosen region of the menu and buys false positives. Expect its
`realized_profit(sim)` to fall well short of its `predicted_profit`, with a
material `loss_making_trades` count; P34's portfolio is calibrated as a sum
and stays much closer to its claim.

Because the market is random per seed, exact numbers vary — the *gap* is the
result.
