# 3. Preparing your data — Menus, Sales, market_type

Reference sample with per-column notes:
[`examples/data/menu_api_sample.xlsx`](../examples/data/menu_api_sample.xlsx)
(the [PDF](../examples/data/menu_api_sample.pdf) is a printout of the same
sheet). Machine-readable variants of a complete tiny request live next to it:
`menus_sample.csv`, `sales_sample.csv`, `market_type_sample.json`, and
`request_sample.json` (the exact `POST /fit` body those three combine into).

## The Menus table

One row per *(key, quantity option)* per decision moment.

**What a menu is.** A menu is the full list of trade options — the *variants* —
that the business faced at one decision moment. Each line item is one option
the business *may* have taken: every quantity/volume that could have been
ordered must be present as its own row, not just the one that was ordered.
One date may have multiple menus, meaning multiple portfolios could have been
assembled at that date (over this REST API each historical *key* must still
appear in exactly one historical menu). The model selects from menus the same
way your business did: one option per group — so representing the *whole*
option space, taken and untaken, is what makes the history usable.

| column | required | meaning |
| --- | --- | --- |
| `key` | yes | any kind of asset/ticker identifier — SKU, contract id, user id, etc. Strings like `A001` are fine (they are re-coded internally and mapped back in the response). |
| `menu` | yes | menu id. `0` = the task menu (T=0 rows only). History: any non-zero id; one menu is the full option list at one decision moment. One date may carry several menus (several portfolios assembled that date). |
| `T` | yes | time: `0` = now (the task), negative = past periods (a week number, a minute — any consistent unit). A key's sales are referenced to its menu's `T`. The sample sheet's note also mentions positive absolute time ids (e.g. unix timestamps); the REST service currently requires the relative convention — task at `T = 0`, history negative, sales `T ≤ 0`. |
| `T_lead` | no | lead time in the same T units: how much time typically passes before any sale can start. Helps reference records from the Sales table. May be blank or absent. |
| *features…* | strongly recommended | any number of feature columns (naïve predictors, signals). **More useful features is better** — see [Features](#features-more-useful-features-is-better). |
| `unit_cost` | **yes** | per-unit landed/acquisition cost — a special column the system interprets as the option's cost. Required and numeric on every row. Also participates in option exclusivity — see [One choice per key-date](#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive). |
| `unit_price` | **yes** | current/historical per-unit selling price — a special column the system interprets as price. If more historical prices are available, add them as *unrolled* feature columns going back in history: `price_T-1`, `price_T-2`, …; a naming pattern like `price1_T-1`, `price2_T-1` distinguishes different price measures when relevant. |
| `*stock*` columns (e.g. `qty_stock`) | no | any column whose name matches the `*stock*` wildcard: the currently open (sellable) position for this key — the amount already in stock. A single market is assumed for all keys, so positions exit FIFO (first in, first out) when there were multiple past orders: profit depends on whether previous stock could be sold (full position close) before the new qty. If no sales of a batch happened, its profit is negative — a full cost write-off. |
| `qty_outstanding_T+1` (`…T+N`) | no | inventory that must enter the FIFO process but is not yet sellable; the `T+N` suffix says it arrives in N time units. `T+0` is impossible by definition — anything already arrived belongs in the `*stock*` column. |
| `qty` | **yes** | the deal-size option this row represents. Integer count-type values (1 apple, 2 apples) **or** floating-point values ($151.50, 38.566 kg) — but not both and not a mixture within one dataset. Required and numeric on every row. Options are **mutually exclusive** within a key-date — see [One choice per key-date](#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive). |
| `historically_available` | no | 1/0 — was this option actually available as a trade option at decision time. `0` marks a **grounded option**: a row whose features and outcome you were able to pre-calculate, but that was not actually selectable in the deal — e.g. only certain quantity combinations were tradeable because of MOQ or pack-size increments. Grounding more outcomes than were selectable is an optional, useful enrichment. |
| `historically_chosen` | history: yes | 1/0 — was this row the option your business actually took. **Exactly one chosen row per (menu, key).** This is what calibrates the model's risk appetite and other business-process behaviors. For deals you declined outright, still include the group and flag the size your process *would* have taken — see [Include the deals you did not take](#include-the-deals-you-did-not-take). |
| `profit` | no | realized total profit of the decision, on the chosen row only. A value here marks the group as an **observed outcome** (labeled context); the number itself is not trusted — the economics are replayed from Sales, so send the Sales rows that produced it. When the precise outcome is unknown, leave it blank and put any *approximate* values in feature columns instead — propagated to **all rows** of the dataset, not just the ones lacking a label. Keep profits as close to the real, money-in-the-bank values as possible, updated with the very latest state of the sales process. **Must be blank on all T=0 task rows** — the task is the prediction target, and the API refuses outcome values for it. |

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

## One choice per key-date: qty and cost are mutually exclusive

The rows of a menu are not independent predictions — they are **mutually
exclusive choices**, and the exclusivity is configured by the *(key, date)*
unique key:

- `qty` is a **mutex** term: the system may select at most one quantity per
  key-date. Two different `qty` values can never be chosen at the same time —
  they are alternatives, not additive positions.
- `cost` behaves the same way whenever it differs within a key-date group: two
  rows with different `unit_cost` under the same key-date are two mutually
  exclusive sourcing options (e.g. two supplier quotes), and the system will
  pick at most one of them.

In short: **the system chooses one option per key-date.** If you need the
model to consider "200 units at $4.10" *and* "500 units at $3.80" as
alternatives, put both rows in the same key-date group; if two positions could
genuinely be taken together, they belong to different keys or different dates.

## Features: more useful features is better

The feature columns of the Menus table are where your market knowledge enters
the model, and the rule is simple: **more useful features is better**. The
input should contain **as many useful features as possible** — naïve
predictors, signals, rankings, velocities, margins, category indicators,
anything your business would glance at before deciding.

Two costs scale with that richness, deliberately: the number of line items in
the historical menus and the number of useful features **directly affect both
model accuracy and the compute time / effort / tokens** a calculation
consumes. Start smaller, measure, then grow the dataset where accuracy pays
for the compute (see [Start small, iterate](#start-small-iterate)).

### Ground ambiguous features into multiple columns

Some features are not facts but *interpretations*, and the interpretation has
free parameters. "Estimated sales velocity from sales rank" is a typical
case: a sales-rank **drop** is an *event*, and re-interpreting an event-like
signal into a per-row feature forces ambiguous decisions — over what time
frame do you measure, and how large must a change be to count as an event in
a noisy signal? There is no single right answer, and whichever translation
you pick silently becomes an assumption of the model.

The recommended practice is to provide **"grounded" versions of ambiguous
features as several columns with different translation settings** — e.g.
`velocity_rank_7d`, `velocity_rank_30d`, `velocity_rank_drop_gt10pct` — and
let the fit find which translation carries signal. This costs input cells but
removes a whole class of silent mis-specification.

### Pull in normalized market history

It is highly recommended to include additional **historical (normalized)
columns — exactly as you would engineer them for a boosting model** — pulled
from market historical data, both for the particular item/key and for the
general market conditions. A typical example: historical price aggregates
(means, minima, percentiles over trailing windows) computed from price data
acquired from an external source provider. These columns give the model the
market context that a single-snapshot menu row cannot carry.

### Set-encoder embeddings (advanced)

Where possible — and if the user permits advanced feature generation — an
agent preparing the input may additionally generate **set-encoder based
embeddings** of items, menus, or market states and attach them as feature
columns.

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

The Sales table is the **money tape**. For the model to function correctly
and with maximum accuracy, it is imperative that it contains the actual money
transferred/recorded in the "sales" tape of your asset-liquidation /
cash-return process — not estimates, not list prices, but what was really
realized. The `profit` values in the historical menus should likewise be
calculated as closely as possible to real values, updated with the **very
latest** state of the sales process (returns, late fees, adjustments), since
the replayed economics are only as honest as this tape.

| column | required | meaning |
| --- | --- | --- |
| `key` | yes | must match a key in the historical Menus. |
| `menu` | no | the menu the sale belongs to (informational). |
| `T` | yes | when the sale happened, same axis as Menus. **Must be ≤ 0** — future-dated sales are rejected. |
| `T_signal_delay` | no | reporting delay of the sales reading vs. when the sale actually happened. Zero delay is assumed when the column is omitted. |
| `qty` | yes | units sold (whole numbers). `0`/blank rows are ignored (they may still carry per-key columns). |
| `price` | format: yes | realized price at sale. The format spec treats it as required for the sales log — it is what lets the model infer price sensitivity on compatible markets and advise price behaviour — though the current wire validator only enforces `key`/`T`/`qty`. Send it. |
| `unit_holding_cost` | no | per-unit storage/holding cost as incurred at that date. If holding costs have changed over time, recalculate historical rows to **current** holding costs. An entire column holding a single constant value is fine. |
| `unit_fee` | no | per-unit extra fee, defined by the identity `price − unit_fee − unit_cost − unit_holding_cost` = net profit per unit. |

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

## Start small, iterate

Dataset size trades directly against compute: line-item count and feature
count drive **both** accuracy and the time/effort/tokens a fit consumes. The
recommended deployment path is iterative:

1. **Start with a simpler, smaller dataset** — fewer keys, fewer feature
   columns, the volume floors above comfortably cleared but not much more.
2. In the [business description](02-endpoints.md#business-description), start
   with **formula-based approximations** of the business cost structure per
   deal/item/asset ("net = price − 15% marketplace fee − $2.10 fulfillment −
   $0.04/unit/week storage"), then move on to more detailed/advanced cost
   structure and business-process documentation in later iterations.
3. Grow menus, features, and grounding richness where measured accuracy pays
   for the added compute — and **plan the deployment in iterations** rather
   than aiming for the perfect first payload.

Along the way, read what the service sends back: beyond `parse_report` and
the counters, the API may occasionally return **rich free-form text
feedback**. If an agentic LLM is assembling your inputs, it should treat that
feedback as instructions to consider and act upon when building the next
iteration of the input.
