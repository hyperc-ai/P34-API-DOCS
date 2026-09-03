# 3. Preparing your data — Menus, Sales, market_type

Reference sample with per-column notes:
[`examples/data/menu_api_sample.xlsx`](../examples/data/menu_api_sample.xlsx)
(the [PDF](../examples/data/menu_api_sample.pdf) is a printout of the same
sheet). Machine-readable variants of a complete tiny request live next to it:
`menus_sample.csv`, `sales_sample.csv`, `market_type_sample.json`, and
`request_sample.json` (the exact `POST /fit` body those three combine into).
[`request_client_grounded_sample.json`](../examples/data/request_client_grounded_sample.json)
is the same market sent the other way — a `profit` on every option row the
caller valued, published verbatim under
[`client_grounded` grounding](02-endpoints.md#bringing-your-own-labels-client_grounded).

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
| `historically_available` | no | 1/0 — was this option actually available as a trade option at decision time. `0` marks a **grounded option**: a row whose features and outcome you were able to pre-calculate, but that was not actually selectable in the deal — e.g. only certain quantity combinations were tradeable because of MOQ or pack-size increments. Grounding more outcomes than were selectable is an optional, useful enrichment. **The column is optional and narrow in scope**: omit it and the whole history reads as real offers, which is what every dataset predating the column meant. It exists to keep an invented quote from being mistaken for one that was made, so it matters only where an *outcome is being replayed* from it. On declined, rejected, and unlabeled rows it changes nothing — see [Availability is not required on unlabeled rows](#availability-is-not-required-on-unlabeled-rows). |
| `historically_chosen` | history: yes | 1/0 — the group's **labeled pick**: the one row whose outcome is known. **Exactly one chosen row per (menu, key)**, because `qty` is a mutex — see [One choice per key-date](#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive). It does **not** have to be a row your business literally took; a history reconstructed by replaying past deals is equally valid. Read [What `historically_chosen` really means](#what-historically_chosen-really-means) before filling this column — it is the single most misread field in the contract. |
| `profit` | no | realized total profit of the decision, on the chosen row only. A value here marks the group as an **observed outcome** (labeled context); the number itself is not trusted — the economics are replayed from Sales, so send the Sales rows that produced it. When the precise outcome is unknown, leave it blank and put any *approximate* values in feature columns instead — propagated to **all rows** of the dataset, not just the ones lacking a label. Keep profits as close to the real, money-in-the-bank values as possible, updated with the very latest state of the sales process. **Must be blank on all T=0 task rows** — the task is the prediction target, and the API refuses outcome values for it. **Under [`client_grounded` grounding](02-endpoints.md#bringing-your-own-labels-client_grounded) this row's rules invert**: send `profit` on *every* historical option row you have valued, not just the chosen one, and the number is taken verbatim rather than replayed. |

Rules the server enforces (violations → HTTP 422 with a specific message):

- menu 0 ⟷ T=0 must agree (no history on menu 0, no task rows off menu 0);
- a fit request must contain T=0 task rows;
- **no ground truth for the task**: any non-blank `profit` on a T=0 row is
  rejected. The predict pipeline has no validation step and never holds
  "actual" values — results contain predictions only;
- each historical key must appear in exactly one historical menu;
- `unit_cost`, `unit_price`, `qty` must be present and numeric.

Messy-but-harmless input is tolerated and *counted* rather than rejected —
blank rows, groups with no chosen row, profits on non-chosen rows (which
[`client_grounded`](02-endpoints.md#bringing-your-own-labels-client_grounded)
keeps rather than discards — there they are the point). "Tolerated"
is not "kept", though: some of those rows never reach the model. Exactly which,
at what granularity, and under which counter is set out in [What intake drops,
and what it reports](#what-intake-drops-and-what-it-reports) — read it before
you conclude a fit trained on everything you sent.

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

## What `historically_chosen` really means

The column's name is historical; its job is not. `historically_chosen = 1`
marks **the one row of a (menu, key) group whose outcome is known** — the row
`profit` attaches to. It is *not* a claim that somebody at the business picked
that line, and the data is not invalid because nobody did.

Fill it mechanically:

- **1** on the row whose profit was safely calculated, predicted, replayed, or
  otherwise obtained as the realized yield of that historical line item.
- **0** on every unlabeled row — profit not calculated, `NaN`, never tested by
  the business or by the market, or a row where replay/simulation would not
  have been safe enough to trust.
- If **several** `qty` options in the same group carry a safely known profit,
  flag the **most profitable** one and leave the rest at 0. Only one `qty` per
  key may be chosen in a menu ([the mutex
  rule](#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive)), so a
  group's label is its best known outcome.
- If **nothing** in the group is safely known, still send the group — it is
  the unlabeled context, and it is required. Put the flag on **any one row** and
  leave `profit` blank on every row. A group with no chosen row at all is
  dropped at intake.

When the history *does* come from a real operator's decisions, flagging what
they actually took is the natural way to satisfy all of the above, and it
carries a bonus: it also calibrates the model to that business's risk appetite
and selection behaviour. That is a nice-to-have, not a precondition.

### On an unlabeled group the flag is a placeholder, not a decision

Earlier editions of this page told you to flag "the size your process *would*
have taken". **Ignore that.** It asked for a counterfactual nobody can source,
and it made a structural requirement look like a research task.

On a group with no outcome, the flag is a **placeholder that keeps the group in
the dataset** — it satisfies the one-per-group invariant and nothing more. Pick
any row: the first, the smallest `qty`, the one your grid centres on. Do not
reconstruct a decision, do not interview anyone about it, and do not withhold
the group because you cannot say what would have been chosen.

This is checkable in the pipeline, not just a stylistic preference. The replay
uses the chosen row's quantity (`business_chosen_qty`, `is_sold_out`) only
inside groups that are **accepted** — those carrying a realized profit. Every
label an unlabeled group produces is gated on `accepted` being true, so which of
its rows wears the flag cannot change any of them.

### Availability is not required on unlabeled rows

`historically_available` and `historically_chosen` answer different questions and
are not a pair. Availability exists so that a quote you *invented* is not
replayed as one that was *made*; it therefore matters only where an outcome is
being derived. On declined, rejected, and unlabeled rows there is no outcome to
derive, so:

- **you do not need to set it** on those rows, or send the column at all;
- **leaving it blank is not a defect** and does not shrink your context — a blank
  reads as `1`, and nothing downstream distinguishes the two on a row that
  carries no label;
- the only hard rule involving it is that `historically_available = 0` and
  `historically_chosen = 1` on the same row is a **422** — you cannot label an
  outcome for an offer you say was never on the table.

Where it does earn its keep is the opposite case: a *labeled* history that mixes
real quotes with rows you generated. Mark the generated ones `0` there, so the
grounding knows which economics are real.

### You do not need an operating history

Because the flag means *labeled*, not *selected*, **P34 applies to a business
that has never traded**. A history assembled entirely from market research and
data collection — menus reconstructed from past market state, outcomes
obtained by replaying or simulating each deal against what the market went on
to do — is a first-class input. Nothing in the model requires a purchase order
behind a labeled row.

What such a history must still supply is the *split*: some line items with a
safe, trustworthy outcome and others with none. Manufacturing that split
deliberately is the interesting part of the job — see [Observed and unobserved
outcomes](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement).

## Include the deals you did not take

P34 fits on the *whole* menu, not just the outcomes you hold. Two kinds of
historical group make up the context:

- **Observed** — groups whose chosen row carries a `profit` value. Their
  economics are replayed from Sales and they become the **labeled** context.
- **Unobserved** — groups with no trustworthy outcome. For an operating
  business these are the deals your process passed on; for a
  research-assembled history they are the line items you could not replay
  safely, or deliberately did not. Either way: flag any one row as
  `historically_chosen` and leave `profit` blank on every row of the group.
  They carry no outcome, and that is the point — they become the **unlabeled**
  context (a group with no chosen row at all is simply dropped at intake, so
  the flag is what keeps them in). Nothing else is asked of these rows: no
  availability flags, no reconstructed decision, no estimated profit.

Both kinds are required, and there are volume floors:

- current model versions refuse a history in which *every* group is observed —
  the fit fails with `Unlabeled business-menu mask selected zero rows`;
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

### How much unlabeled context is enough

Note what the floors above are, and what they are not. They are **absolute
counts on the observed side** — enough labeled deals for the regressor to have
something to fit. They are **not a ratio**, and there is no requirement anywhere
that the labeled rows outnumber the available options, or reach any particular
share of them. A history of thousands of options with a few hundred outcomes
among them is entirely normal and entirely fine.

The requirement that does bind runs the other way, and only the last of the
floors above touches it — by rejecting the zero case. **The declined, rejected,
and untested options must be present in quantity, not merely present.**

Here is why the zero check is not enough. If your history shows almost every
option being taken, then what it describes is a market in which taking
everything was the right move — and on that data, "take everything" *is* the
profit-maximising policy. The model will learn it, faithfully. But a take-all
optimum is an artefact of a history that never recorded a refusal; it is false
of essentially every real market, where capital, capacity, shelf life, and
counterparty risk make some deals worth declining. P34's product is the
refusals, and a history without enough of them gives it nothing to refuse with.

There is no server-side threshold for this — intake checks only that the
unlabeled context is non-empty, and the cluster only that it is non-zero. It is
on you. Practically: aim for the unlabeled groups to be a **substantial share of
the history, comparable to or larger than the observed ones**, and treat a
history that is 90-odd percent observed as a data-collection problem rather than
a payload ready to send. It will pass every check and then recommend that you
buy everything.

If your market genuinely reveals almost every outcome, you are not out of
options — you are in the case that [observed and unobserved
outcomes](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement)
is about, where the split has to be constructed rather than found.

`POST /fit` validates shape, not statistics — both conditions surface only
when the calculation runs; see
[Fit-time failures](04-errors-and-checks.md#fit-time-cluster-failures).

## What intake drops, and what it reports

Some of what you send does not reach the model. This is worth stating precisely
rather than in passing, because the largest of these drops is at *group*
granularity and is easy to trigger by accident.

First, the scope of the word "drop". **Nothing is deleted anywhere.** Your
payload is not modified, nothing is written back, and no stored copy of your
data is altered. The drop happens while parsing one request into one training
context and applies to that request only: fix the input, resubmit, and every row
returns. Every drop is also **counted and returned to you** in `parse_report` on
the same response — none of it is silent, though all of it is easy to not read.

| `parse_report` counter | granularity | what goes, and why |
| --- | --- | --- |
| `menus_rows_dropped_incomplete` | **row** | rows with a blank `key`, or a non-numeric `T` or `qty`. These cannot be placed in a menu or a group at all. If it takes *every* row, the request is a 422 instead. |
| `menus_rows_dropped_no_choice` | **group — every row of it** | historical `(menu, key)` groups without exactly one `historically_chosen = 1`. Zero chosen rows → the entire group is removed, however many quantity options it held. (Two or more chosen rows is a 422, not a drop.) **This is the one that costs you real context** — see below. |
| `profit_values_ignored_on_non_chosen` | **cell** | a `profit` written on a row that is not the group's chosen row. The row survives; only the number is discarded, because the derived modes are about to recompute it. Always `0` under [`client_grounded`](02-endpoints.md#bringing-your-own-labels-client_grounded), which keeps every one of those values and reports them as `client_labeled_rows` instead. |
| `sales_rows_dropped_unknown_key` | **row** | Sales rows whose `key` is absent from the surviving historical menus. Note the cascade: a key that vanished with a no-choice group takes its sales with it, under *this* counter, not the menus one. |
| `sales_rows_dropped_zero_or_blank_qty` | **row** | Sales rows with `qty` of 0 or blank. `unit_fee` is harvested from them **before** they go, so per-key fee rows that carry no quantity still do their job. |
| `client_grounding_rows` | — | not a drop at all: how many rows carried `historically_available = 0`. Informational. |

**Why the no-choice drop is worth checking every time.** The flag column is
coerced leniently — anything non-numeric, and any blank, becomes `0`. So a
mis-typed header, a boolean exported as `TRUE`/`FALSE`, a locale that wrote
`1,0`, or a transform that filled the column only for the deals that were taken,
all produce the same outcome: groups with no flag, removed whole. The counter is
the only visible symptom, and if enough goes this way the fit then fails on a
volume floor for a history you believed you had sent.

Guard against it client-side rather than after billing:

```python
g = hist.groupby(["menu", "key"])["historically_chosen"].sum()
assert (g == 1).all(), g[g != 1]
```

Everything a *labeled* group carries is kept: the non-chosen quantity options of
an observed group are the counterfactuals, and they go to the model in full.

> **On the design of the no-choice drop.** Discarding a customer's rows to make
> a request parse is a defensible convenience and a poor default, and we take the
> point. A group with no flag is far more often an input the sender got wrong
> than an intentional submission, and refusing it at the door — a 422 naming the
> groups, the way every other structural mistake in this table is treated — would
> surface it before the session is billed rather than in a counter afterwards.
> Changing it is an API-behaviour change for every existing client, so it is not
> something this page can do unilaterally; it is on the list. Until then, the
> pre-flight check above is the reliable defence.

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
| `qty` | yes | units sold. `0`/blank rows are ignored (they may still carry per-key columns). Whole numbers are the usual case and the only thing some market types accept (`synthetic_inventory` rejects fractions), but the wire itself only requires `qty > 0` — so **if your `profit` was computed from a fractional quantity, send the fraction**. See [The tape and the profit must agree](#the-tape-and-the-profit-must-agree). |
| `price` | format: yes | realized price at sale. The format spec treats it as required for the sales log — it is what lets the model infer price sensitivity on compatible markets and advise price behaviour — though the current wire validator only enforces `key`/`T`/`qty`. Send it. |
| `unit_holding_cost` | no | per-unit storage/holding cost as incurred at that date. If holding costs have changed over time, recalculate historical rows to **current** holding costs. An entire column holding a single constant value is fine. |
| `unit_fee` | no | per-unit extra fee, defined by the identity `price − unit_fee − unit_cost − unit_holding_cost` = net profit per unit. |

A sale is attributed to the key's menu: its replay week is `T − T(menu)`, and
must fall within the write-off horizon set in `market_type`. Every sale must
already have happened (`T ≤ 0`) — the pipeline refuses future information.

### The tape and the profit must agree

Grounding **replays** your Sales tape to reproduce the `profit` you reported on
each chosen menu row, and compares the two. Both numbers can be individually
correct and the fit will still fail if they were computed from *different*
quantities. The most common way that happens is an export step:

- realized sales were fractional (weight, volume, continuous demand, a modelled
  fill) and the tape was **rounded to whole units** on the way out;
- the tape was aggregated, truncated to a shorter window, or reconstructed from
  a different system than the one that produced `profit`;
- `profit` came from an authoritative ledger while the tape came from an
  operational feed that never quite matches it.

The replay has only the tape. It cannot recover the quantity your accounting
actually used, so it produces a different profit and reconciliation fails with
`bg_replay_ground: reconciliation failed`.

**Recognising it.** Rounding noise and a wrong formula look nothing alike:

| | lossy tape | wrong profit model |
| --- | --- | --- |
| which rows disagree | an identifiable subset (the keys the export touched) | spread across all rows |
| direction | **two-sided** — model too high on some rows, too low on others | **one-signed** — a missing or extra cost term biases every row the same way |
| size | bounded by the rounding step — at most about one unit × `unit_price` per row | scales with the missing component |
| worst rows | the **smallest** `qty` — on a 1-unit order, one unit of rounding is the difference between selling at margin and writing off at cost, i.e. a sign flip |

If rows without the export problem reconcile *exactly*, the model is right and
the tape is the problem.

**Fixing it.** In order of preference:

1. **Send the quantity your `profit` was computed from**, fractional if that is
   what it was. The wire accepts it (`qty > 0` is the only rule). Check your
   `market_type` first — `synthetic_inventory` requires whole units, so a
   fractional tape needs a business-led fit with a compiled adapter.
2. **Or recompute `profit` from the tape you can actually export.** If whole
   units are a hard constraint, make the label agree with the tape rather than
   the other way round. Consistency matters more than which of the two is more
   "true" — the model learns the economics you demonstrate.
3. **Only if neither is possible**, say so in your business description,
   naming the affected keys and the size of the discrepancy, and contact
   support: a market whose realized profits genuinely diverge per row can be
   moved to an advisory reconciliation policy per account. It is not automatic,
   and it is not a way around a fixable export — the same lossy tape also
   generates the counterfactual labels for every quantity you did *not* choose,
   so those rows carry the error too.

Describing the rounding in your business description does **not** exempt the
fit: the gate is arithmetic on your numbers, not a reading of your prose.

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

**"Small" means shallow, not narrow.** Start with fewer feature columns and a
shorter history — never with a narrower live menu. The task menu still has to
carry the market's full flow of candidate deals, hundreds at the least, because
a handful of hand-picked options is not a small dataset: it is a sign that the
market, the collection mechanism or the plan is wrong. See [reject markets, at
scale](01-overview.md#where-the-theory-meets-reality-reject-markets-at-scale).

Along the way, read what the service sends back: beyond `parse_report` and
the counters, the API may occasionally return **rich free-form text
feedback**. If an agentic LLM is assembling your inputs, it should treat that
feedback as instructions to consider and act upon when building the next
iteration of the input.
