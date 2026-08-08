# 3. Preparing your data — Menus, Sales, market_type

Reference sample with per-column notes:
[`examples/data/menu_api_sample.xlsx`](../examples/data/menu_api_sample.xlsx)
(the [PDF](../examples/data/menu_api_sample.pdf) is a printout of the same
sheet). Machine-readable variants of a complete tiny request live next to it:
`menus_sample.csv`, `sales_sample.csv`, `market_type_sample.json`, and
`request_sample.json` (the exact `POST /fit` body those three combine into).

## The Menus table

One row per *(key, quantity option)* per decision moment.

| column | required | meaning |
| --- | --- | --- |
| `key` | yes | asset/ticker id — SKU, contract id, etc. Strings like `A001` are fine (they are re-coded internally and mapped back in the response). |
| `menu` | yes | menu id. `0` = the task menu (T=0 rows only). History: any non-zero id; one menu is the full option list at one decision moment. |
| `T` | yes | time: `0` = now (the task), negative = past periods. A key's sales are referenced to its menu's `T`. |
| `T_lead` | no | lead time in T units before sales can start. |
| *features…* | your call | any number of feature columns (naïve predictors, signals). |
| `unit_cost` | yes | per-unit landed cost. |
| `unit_price` | yes | current/historical unit price. |
| `qty` | yes | the deal-size option this row represents. |
| `historically_available` | no | 1/0 — was the option available at decision time. |
| `historically_chosen` | history: yes | 1/0 — was this row the option your business actually took. **Exactly one chosen row per (menu, key).** For deals you declined outright, still include the group and flag the size your process *would* have taken — see [Include the deals you did not take](#include-the-deals-you-did-not-take). |
| `profit` | no | realized total profit of the decision, on the chosen row only. A value here marks the group as an **observed outcome** (labeled context); the number itself is not trusted — the economics are replayed from Sales, so send the Sales rows that produced it. Leave blank when the outcome was not observed. **Must be blank on all T=0 task rows** — the task is the prediction target, and the API refuses outcome values for it. |

Rules the server enforces (violations → HTTP 422 with a specific message):

- menu 0 ⟷ T=0 must agree (no history on menu 0, no task rows off menu 0);
- a fit request must contain T=0 task rows;
- **no ground truth for the task**: any non-blank `profit` on a T=0 row is
  rejected. The predict pipeline has no validation step and never holds
  "actual" values — results contain predictions only;
- each historical key must appear in exactly one historical menu;
- `unit_cost`, `unit_price`, `qty` must be present and numeric.

Messy-but-harmless input is tolerated and *counted* rather than rejected —
blank rows, groups with no chosen row, profits on non-chosen rows — see
`parse_report` in the fit response for exactly what was dropped or ignored.

## Include the deals you did not take

P34 fits on the *whole* menu, not just your wins. Two kinds of historical
groups make up the context:

- **Observed** — groups whose chosen row carries a `profit` value. Their
  economics are replayed from Sales and they become the **labeled** context.
- **Declined** — deals your process passed on. Include them too: flag the
  size your process *would* have taken as `historically_chosen` and leave
  `profit` blank on every row of the group. They carry no outcome, and that
  is the point — they become the **unlabeled** context that teaches the
  model your selection pattern (a group with no chosen row at all is simply
  dropped at intake, so the would-be flag is what keeps them in).

Both kinds are required, and there are volume floors:

- current model versions refuse a history that is all wins — the fit fails
  with `Unlabeled business-menu mask selected zero rows`;
- at least ~100 observed groups must share a qty option, or the fit fails
  with `NotEnoughData: No qty values have at least 100 rows`;
- the history must span enough **decision moments**: a toy history of one or
  two menus fails with `ParmlInsufficientDataError: Not enough valid menus to
  train on` — provide at least ~10 historical menus (50+ recommended);
- each menu needs a healthy count of **observed deals**: internal fit
  candidates with fewer than ~10 outcome-carrying deals are skipped, and if
  every candidate is skipped the fit fails with `No FC-fit universe had
  enough rows to fit an FC regressor` — aim for 20+ observed deals per menu.

As a rule of thumb: **hundreds of observed deals spread over a dozen or more
menus** is the practical minimum; real business histories clear these floors
easily, toy payloads usually don't.

`POST /fit` validates shape, not statistics — both conditions surface only
when the calculation runs; see
[Fit-time failures](04-errors-and-checks.md#fit-time-cluster-failures).

## The Sales table

| column | required | meaning |
| --- | --- | --- |
| `key` | yes | must match a key in the historical Menus. |
| `menu` | no | the menu the sale belongs to (informational). |
| `T` | yes | when the sale happened, same axis as Menus. **Must be ≤ 0** — future-dated sales are rejected. |
| `T_signal_delay` | no | reporting delay of the sales reading. |
| `qty` | yes | units sold (whole numbers). `0`/blank rows are ignored (they may still carry per-key columns). |
| `price` | no | sale price. |
| `unit_holding_cost` | no | per-unit holding cost at that time (a constant column is fine). |
| `unit_fee` | no | per-unit extra fee; `price − unit_fee − unit_cost − unit_holding_cost` = net profit per unit. |

A sale is attributed to the key's menu: its replay week is `T − T(menu)`, and
must fall within the write-off horizon set in `market_type`. Every sale must
already have happened (`T ≤ 0`) — the pipeline refuses future information.

## market_type

```json
{
  "market_type": "synthetic_inventory",
  "parameters": {
    "qty_ordered_range": 40,
    "inventory_holding_weeks_before_writeoff": 8,
    "holding_cost_per_unit": 0.5,
    "leftover_writeoff_fraction": 1.0,
    "grounding_labelling_mode": "synthetic_full"
  }
}
```

`inventory_holding_weeks_before_writeoff` is the replay horizon: how many T
units inventory may sell before the leftovers are written off. It also bounds
how far after its menu a sale row may be dated.
