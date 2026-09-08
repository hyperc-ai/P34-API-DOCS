---
name: p34-prepare-inputs
description: Use when turning a business's recorded history and its current purchase/allocation options into the P34 Menus and Sales tables for a `/fit` — keeping recorded observations intact, leaving unknown outcomes blank, enumerating every currently executable quantity, and reporting coverage and provenance. Load before writing any contract table, and whenever a request asks you to rebalance, prune, weight or otherwise reshape the data.
---

# Prepare P34 inputs

## What this covers

You are mapping a caller's own records into the two tables `POST /fit` takes:
**Menus** (one row per key × quantity option per decision moment) and **Sales**
(the realized money tape). The column contract — every column, its type, and
the rules the server enforces — is
[docs/03-data-format.md](../../docs/03-data-format.md). **Read it and link to
it. Never restate the column tables**; they are the source of truth and they
change.

This skill adds what a column table cannot say: how to keep the caller's
evidence intact while mapping it, and how to establish that the current option
set is complete. The long form, including what each service mode does with a
missing previous-choice flag, is in
[references/history-contract.md](references/history-contract.md).

**The rule everything else follows from:** Menus is a record of what the
business could have done and what actually happened. The model learns the
sample you demonstrate, so any edit that makes the sample *look* better makes
the result worse.

## Workflow

### 1. Inventory the sources and leave them unmodified

List every artifact the tables will be built from — recorded menus/offers,
the sales tape, the current offer or availability schedule, price/fee
schedules, the caller's request. For each one record where it came from, when
it was produced, and enough identity to detect a change later (a checksum, a
size, an export timestamp).

Never edit a source in place. Read it and write new files; the prepared tables
are derived artifacts and stay separate from the evidence. If a source is
wrong, say so in the report — do not correct it silently.

### 2. Map the recorded history verbatim

Every historical option row that was on the table goes into Menus **once**,
with its recorded economics and granularity: the quantities that were offered,
the unit costs that applied to each, the price, and the outcome where one is
known.

- Keep the rows the business **did not** take. Declined and untested options
  are the context the fit needs — see
  [Include the deals you did not take](../../docs/03-data-format.md#include-the-deals-you-did-not-take).
- An outcome you do not know is **blank**, never `0`. `0` is the claim "this
  was tried and returned nothing", and the model believes it. A downstream
  tool that dislikes blank cells is a problem on that tool's side of the line,
  not a reason to write a number into the evidence.
- Do not add a `historically_chosen` flag you do not have a record for. The
  column is optional; read
  [Your previous business policy](../../docs/03-data-format.md#your-previous-business-policy-what-historically_chosen-marks)
  and the mode table in
  [references/history-contract.md](references/history-contract.md#missing-historically_chosen-what-each-mode-does).
- Leave a source `T` axis alone when it already satisfies the contract (task
  at `0`, history negative, sales `T ≤ 0`). If it genuinely must move, shift
  every Menus and Sales row by the same offset and report the shift — never
  re-derive the axis from dates or intervals you inferred.
- Sales rows pass through with the money that was actually recorded. Do not
  round, aggregate or re-derive a tape that a `profit` was computed from — see
  [The tape and the profit must agree](../../docs/03-data-format.md#the-tape-and-the-profit-must-agree).
- If you must reduce the history to fit a budget, take **whole consecutive
  most-recent menus**, never a selection of rows, and report the window you
  kept and what you dropped.

### 3. Build the T=0 task menu from the current option schedule

The task menu is `menu = 0`, `T = 0`, and it must carry **every quantity option
that is executable right now** for each candidate, each with the cost and terms
that actually apply to it — stock limits, minimum order quantity, pack
increments, and every tier or break price.

A source schedule is usually **not** a list of rows. A supplier quotes *tiers*
("1–3 at 6.40, 4 and up at 5.80") against a stock or credit limit; a venue
quotes a step size and a cap. Expand it: one row per executable quantity
inside each tier, at that tier's cost, truncated by whichever limit actually
binds. Two tier lines are two prices, not two options — a task menu built by
copying them offers the model two of the choices the business really has.

- Do **not** drop a feasible option because it is larger than anything in the
  history, has no historical support, looks unattractive under a rule of
  thumb, or because the caller says they would not pick it. Choosing among the
  options is the fit's job; an option missing from the task menu is one the
  model can never return. Thin historical support is a fact to report, not a
  reason to delete a real choice.
- A stated business constraint that makes an option genuinely **unavailable**
  is different — that option was never on the table, and leaving it out is
  accurate. Record which constraint removed it.
- Do **not** invent history to make a feasible quantity look supported.
- `profit` stays **blank** on every T=0 row — the server rejects a fit
  otherwise. Feasibility and forecast confidence are different statements:
  record confidence, if you have it, in a feature column or the report.
- Keep the source availability schedule alongside the tables, and keep a
  coverage record mapping each feasible quantity and tier price in it to the
  emitted row.

### 4. Economics, labels and features

Ordinary business economics are yours to compute: fee and cost formulas,
recorded rates, landed cost, quantity-weighted business statistics, and modest
decision-time features. Carry feature columns on **all** rows of the dataset.

Keep four things distinguishable in the report: measured facts, values you
calculated from them, estimates, and unknowns. A speculative demand or profit
estimate belongs in a named feature column — never in a historical `profit`
and never on a T=0 row.

### 5. Do not compensate for the sample, and say when you were asked to

P34 is pre-trained to work on raw records; it needs no loss weighting and no
balance signal, and a compensated sample simply misdescribes the market.

**No transformation whose purpose is statistical compensation:** no
outcome-selective removal, no class balancing, no over- or undersampling, no
duplicated or synthetic observations, no invented labels, and no weight or
feature column whose purpose is to compensate for the observed sample
distribution.

This is not a ban on ordinary work: formula columns, recorded cost rates,
faithful format mapping, and quantity-weighted business statistics are all
fine, and required format changes still keep every source record.

When a request asks for one of these — "balance the losing cases", "duplicate
that row so it counts more", "add a weight column so the loss counts double",
"drop the outliers" — do not perform it, and do not substitute a different
compensation for the one that was refused. Name what you declined and why in
the report, and offer what does help instead: more recorded history, more
untaken options, better features.

### 6. Report coverage and provenance

The contract tables carry contract columns and your feature columns — nothing
else. Provenance, coverage and caveats go in a separate coverage and
provenance record: a section of the deliverable, or its own file when the
caller asks for one. It states:

- each source artifact by name, and what it contributed;
- that the current option set is complete — how many feasible options the
  schedule implies once its tiers and limits are expanded, and that all of
  them are present, including every tier price;
- **the historical-support gap, stated separately from feasibility**: which of
  those options the recorded history has never covered, and that they are on
  the menu regardless. These are two different facts about the same row, and
  collapsing them is how a feasible option quietly disappears;
- the history window kept and anything omitted, with the reason;
- every requested change you declined, and why;
- what you could **not** verify. A reader cannot prove completeness from the
  submitted rows alone; without a source schedule to compare against, report
  "cannot verify completeness", never a pass.

Keep it as short as the caller wants — but a request you declined is never
the part you leave out. Someone reading the tables later has no other way to
learn that a change was asked for and not made, and a silent refusal looks
identical to a missed instruction.

### 7. Self-check before handing the tables on

- sources unchanged since step 1 (compare the recorded checksums);
- historical rows appear once each, with recorded values;
- unknown outcomes blank, no `0` placeholders;
- T=0 rows: `menu = 0`, every feasible quantity/cost pair present, `profit`
  blank;
- at most one `historically_chosen = 1` per `(menu, key)`, and no flag
  invented;
- Sales `T ≤ 0`, quantities as recorded;
- the report names its sources, its coverage, and its refusals.

## Cases with no supported answer

Say so explicitly rather than inventing a policy — see
[references/history-contract.md](references/history-contract.md#cases-with-no-supported-answer).
Two come up often: a **continuous or very large quantity space** has no
published completeness policy (do not quantise it, do not invent interval
fields), and a **zero-quantity input row** is not implied by the fact that a
zero output means abstain (input zero follows the published contract; ask if
it is ambiguous).

## Optional, not prerequisites

Richer feature work pays off and the contract documents it, but none of it is
required to send a correct first fit. When the caller wants it, read
[Features](../../docs/03-data-format.md#features-more-useful-features-is-better),
[Ground ambiguous features into multiple columns](../../docs/03-data-format.md#ground-ambiguous-features-into-multiple-columns),
[Pull in normalized market history](../../docs/03-data-format.md#pull-in-normalized-market-history)
and
[Set-encoder embeddings](../../docs/03-data-format.md#set-encoder-embeddings-advanced).
The recommended path is
[Start small, iterate](../../docs/03-data-format.md#start-small-iterate):
a shallow history with few features first — never a narrower live menu.
