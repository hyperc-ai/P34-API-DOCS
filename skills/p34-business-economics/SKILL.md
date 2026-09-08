---
name: p34-business-economics
description: Use when writing the `business_description` for a P34 `/fit` and working out the unit economics behind it — the caller's real fees, costs, lead times and horizons, the outcomes their own records already support, and which numbers are measured, calculated, estimated or unknown. Load before reusing a description from another project, and before writing any forecast into a table.
---

# P34 business economics and descriptions

## What this covers

A `/fit` carries two things only the caller can supply: the tables (build them
with [p34-prepare-inputs](../p34-prepare-inputs/SKILL.md)) and a description of
the business those numbers came from. Under the default mode that description
is **executable input, not metadata** — read
[Business description](../../docs/02-endpoints.md#business-description) and
[What to write in it](../../docs/02-endpoints.md#what-to-write-in-it), and link
to them rather than restating the field, its resolution order or its modes.

This skill is the part the contract cannot state: how to get the caller's
*actual* terms, what is cheap to calculate from them, and how to keep an
estimate out of a cell the service will read as an observation.

**The rule everything else follows from:** ordinary business economics are the
caller's, and the heavy work is the service's processing. Send the values your
records support, and label everything else for what it is.

## Workflow

### 1. Collect the actual terms

Ask the caller for the unit economics, or research the market with the maximum
effort available — the docs are explicit that a thin description degrades the
result. Collect, and make each of these a line in the description:

- **decision and units** — what is being chosen, in what unit, how often, and
  whether the unit is a whole count or a fractional amount;
- **costs and fees** — acquisition or landed cost, revenue share or commission,
  per-order and payment charges, storage, anything deducted before the money
  lands;
- **timing and inventory constraints** — lead time, pack size or minimum order,
  stock already held, and how long stock may sit before it is written off;
- **outcome and horizon treatment** — what counts as the outcome of a decision,
  over what window it is measured, and what happens to what does not sell;
- **the formulas**, and which column each term maps to;
- **sources, and material unknowns** — including whether recorded sales were
  **stock-limited**: a group that sold out measures the stock, not the demand,
  and nothing in that history says how much more would have sold.

Never carry a description, fee schedule or formula over from another project,
another client or a worked example. A rate that was true elsewhere is an
invented term here, and the service will compile it as if it were real. A
template you are handed is a draft to check line by line against the terms you
were actually given; keep the lines that match and rewrite the rest. A market
name, a link to a playbook, or last quarter's text edited at the top is not a
description of this request.

### 2. Map the business concepts to contract columns

Per-unit acquisition cost is `unit_cost`, selling price is `unit_price`, the
deal size is `qty`; the Sales tape carries `unit_fee` and `unit_holding_cost`,
lead time is `T_lead`, open position goes in a `*stock*` column, and the
write-off horizon is `inventory_holding_weeks_before_writeoff` in
[`market_type`](../../docs/03-data-format.md#market_type). The column meanings
are in [the Menus table](../../docs/03-data-format.md#the-menus-table) and
[the Sales table](../../docs/03-data-format.md#the-sales-table) — read them
there.

The fee identity is the one worth memorising, because most cost structures
collapse into it: `price − unit_fee − unit_cost − unit_holding_cost` is net
profit per unit. A percentage fee becomes a per-unit number at a stated price;
say which price you used.

A term with no column of its own belongs in the description — that is what the
description is for — and, when it varies row by row, additionally in a named
feature column.

### 3. Calculate the values the records support

Start with formula-based approximations of the cost structure and deepen them
over iterations ([Start small, iterate](../../docs/03-data-format.md#start-small-iterate)).
The cheap, defensible ones:

- **realized outcomes**, from a recorded tape and recorded terms. A group whose
  tape shows `q` units sold at price `p`, bought at recorded cost `c` under a
  fee rate `f`, realized `(p × (1 − f) − c) × q`. Where a payout or settlement
  statement exists, compute it that way too and check the two agree.
- **rates you can recompute.** Where a payout, invoice or settlement record
  shows the money that actually moved, derive the rate from it instead of
  taking a stated one on trust, and compare the two. A rate somebody states is
  a belief; a rate the records reproduce is a measurement. When they disagree,
  the measurement is the term: use it, keep the stated one in the write-up as
  what was believed, and say in the description which one the numbers used and
  why. Silently adopting the stated rate, or silently dropping it, both leave
  the reader unable to tell that there was a question.
- **per-unit economics** — fee-adjusted price, net margin, landed cost.
- **modest decision-time features** the business would glance at anyway.

Write them where the contract puts them:
[Where `profit` goes](../../docs/03-data-format.md#where-profit-goes). Keep the
tape and the label consistent with each other — the check is arithmetic on your
numbers, not a reading of your prose
([the tape and the profit must agree](../../docs/03-data-format.md#the-tape-and-the-profit-must-agree)).

Do not build a demand model, a replay implementation, a parameter sweep or a
grid of predictors to fill a cell. If an outcome needs an assumption the records
do not carry, it is not supported — leave it blank and say so.

### 4. Label every number: measured, calculated, estimated, unknown

Keep the four apart in the record you save with the request, and keep them apart
in the tables:

| kind | what it is | where it goes |
| --- | --- | --- |
| measured | off the tape, the ledger, the payout statement, or a stated term the records bear out | the column that holds it, as recorded |
| calculated | derived from measured values and recorded terms by a formula you state | the column, with the formula written down |
| estimated | forecasts, backcasts, priors, anything with a free parameter | a **clearly named feature column**, carried on all rows |
| unknown | no defensible value | **blank** |

Name the unknowns rather than omitting them: a number you did not have is a
line in the record like any other, and a reader who cannot see the gap will
assume you closed it.

An estimate never becomes an outcome. A forecast — even one the client's own
analyst produced, even one already labelled "expected profit" — must not land in
a historical `profit`, and `profit` is blank on every T=0 row because the task is
the prediction target. `0` is never a stand-in for unknown: it is the claim that
something was tried and returned nothing.

### 5. Reconcile the description against the tables

The description and the tables have to describe the same business:

- every rate the description states is the rate the numbers used — if the text
  says a 10% commission, a label computed with 15% is a defect in one of the
  two, and the recorded outcomes already in the tables are a check on both;
- units, cadence and horizon match the `T` axis and the `market_type` parameters;
- the `market_type` named is one you can actually support, and any parameter it
  takes describes the same horizon the description describes;
- values you could not verify are named as unverified rather than smoothed over.

### 6. Save it, and send it in the documented field

Keep the description with the request that used it, so a later reader can see
which text produced which labels. Send it as the top-level
`business_description`, or maintain it in the console profile and send requests
without the field — both are documented in
[Business description](../../docs/02-endpoints.md#business-description).

Under [`client_grounded`](../../docs/02-endpoints.md#bringing-your-own-labels-client_grounded)
the description is **optional**: nothing is compiled from it and nothing is
replayed, so none of the replay-side requirements apply there. Writing one is
still the cheapest way to make your own labels reviewable, but it is not a
prerequisite, and this skill adds none.

## Optional, not prerequisites

Richer feature work pays off and the contract documents it
([Features](../../docs/03-data-format.md#features-more-useful-features-is-better)),
but a correct first request needs only the terms, the supported values and the
description. Exhaustive feature generation is not this skill's job, and it is
not a condition of sending a fit.

## Market-specific assistance

An agent working inside a HyperC member workspace may find market playbooks
there — fee schedules, collection notes and description checklists for specific
markets — which are useful shortcuts for step 1. This skill does not depend on
them: every rule above works from the caller's own terms alone, and a playbook's
default never outranks a term the caller actually stated.
