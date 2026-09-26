---
name: p34-interpret-results
description: Use when a P34 `/fit` has returned a `done` result and it has to become something a business can execute — mapping the returned quantities back to real offers, listing the refusals, reading the parse report that says what the fit was actually given, and stating how far the predicted profit can be trusted. Load before quoting a returned number to anyone, and whenever your own estimate disagrees with the result.
---

# Interpret a P34 result

## What this covers

You have a `done` response from `GET /result/{session_id}` and someone has to
act on it. The response shape, the menu semantics and the confidence fields
are in
[Result statuses](../../docs/02-endpoints.md#result-statuses) and
[Confidence correction](../../docs/02-endpoints.md#confidence-correction);
the row-count and `parse_report` fields are in
[Fit response fields](../../docs/04-errors-and-checks.md#fit-response-fields).
**Read them and link to them. Never restate the field tables** — they change.

This skill is the part the field tables cannot say: how to turn the returned
rows into orders without adding anything the fit did not return.

**The rule everything else follows from:** the answer is the set of rows the
result carries — the sizes it chose *and* the refusals, together. Anything you
add to it, drop from it, or substitute into it is your own number, and it has
to be labelled as yours.

Getting here: [p34-prepare-inputs](../p34-prepare-inputs/SKILL.md) built the
tables, [p34-business-economics](../p34-business-economics/SKILL.md) the
description, and [p34-submit-and-monitor](../p34-submit-and-monitor/SKILL.md)
carried the request to a result.

## Workflow

### 1. Read the provenance and the fields the response actually carries

A free-tier supported-market result follows the normal fit/result workflow.
Interpret its returned menu and provenance as supplied. Do not invent missing
prediction, training, calibration, confidence, runner-model, or row-count
fields, and do not treat their absence as an error unless the response contract
requires them.

For a P34 model result, read `parse_report` before you read the menu.

The counters say what the fit was actually given, and that changes what its
answer means. Take them from the response, not from what you believe you sent:

- **drop counters** — rows that never reached the model. A non-zero counter is
  a fact about this result and belongs in the write-up, not a footnote you
  leave out because the numbers still look fine.
- **`historically_chosen: "absent"`** — your column flagged nothing, so every
  historical group fell back to the default business choice and the fit had no
  record of what the business actually took. Read
  [your previous business policy](../../docs/03-data-format.md#your-previous-business-policy-what-historically_chosen-marks);
  an unexpected `absent` usually means a `TRUE`/`FALSE` export.
- **`labeled_rows` / `unlabeled_rows` / `task_menu_rows`** — the size and shape
  of what was fitted, and whether every option you sent arrived. A thin
  unlabeled share is the condition that trains a take-all policy, so it is a
  caveat on *these* recommendations — see
  [how much unlabeled context is enough](../../docs/03-data-format.md#how-much-unlabeled-context-is-enough).

### 2. The `qty > 0` rows together are the portfolio

Read `predicted_profit_sum` as the portfolio total with the profit basis
reported by the response; `n_selected` counts the selected positions. A line
pulled out of the set on its own is no longer the portfolio the response
scored. Report the meaning supplied by the response, and do not infer model
prediction provenance from the field name alone.

### 3. The refusals are the product, so write them down

Two different rows mean *do not trade*, and both belong in the deliverable:

- a returned row with `qty: 0`; and
- **a key that is not in the returned menu at all.** On current model versions
  the response carries only the keys of the chosen scenario, so an absent key
  means do not trade, exactly like a zero
  ([Result statuses](../../docs/02-endpoints.md#result-statuses)).

Say which keys were refused and which kind of refusal it was. A reader cannot
tell a refusal from an oversight unless the write-up says so, and the refusals
are the part of the answer that is hardest to reproduce anywhere else.

### 4. One choice per key

The menu rows are mutually exclusive alternatives — the system selects at most
one quantity, and at most one cost, per key-date
([one choice per key-date](../../docs/03-data-format.md#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive)).
If your proposal carries a key twice, one of those lines is yours, not the
model's.

### 5. Map each returned (key, qty) to an offer you can actually execute

The result names a size, not a purchase. Join it back to the source schedule
and carry the row that will really be bought: its identifier, the cost that
applies **at that size** — the covering tier, not the key's opening tier — and
the terms that come with it (lead time, minimum, pack increment).

- If a returned size is no longer executable — the offer moved, stock went,
  the tier closed — say so and hand it back for a decision. Do **not** round it
  to the nearest size the fit did not return.
- If the executable cost differs from the `unit_cost` the fit was given, the
  prediction was made on the old number. Report the difference; it is a reason
  to refit, not a reason to edit the result.

### 6. Say how far the number can be trusted, even when nobody asked

`predicted_profit_sum` is a calibrated prediction over a fitted distribution,
not a forecast anyone owes you. Give it its context in a line or two:

- the profit time frame and write-off/residual-value policy saved with this
  request; distinguish retained accounting value from cash recovered, and do
  not compare results with different horizons as though they measured the same outcome;
- the applied selection threshold — `confidence_thresh_calibrated`,
  `confidence_correction`, `confidence_thresh_effective`;
- the `confidence_sweep`: what the portfolio would have been at other
  corrections. Two points are enough to show whether the selection is stable
  or hangs on the setting, and it is the cheapest way to choose the next fit's
  correction ([Confidence correction](../../docs/02-endpoints.md#confidence-correction));
- the limits already found in step 1 — history span, unlabeled share, dropped
  rows, and how much of your task menu was actually scored.

A request for brevity shortens this to a sentence. It does not remove it: a
number presented with no uncertainty is a different claim from the one the
service made.

### 7. Your own estimate sits **beside** the result, never inside it

A replay, a margin spreadsheet, an analyst's sizing — all of these are useful
sanity checks, and worth recording next to the result with the disagreement
stated plainly. None of them is a P34 output.

Where yours disagrees, **the proposal still carries the quantity the fit
returned.** Substituting your size and presenting the result as P34's is the
one error nobody downstream can catch: the artifact looks exactly like a real
recommendation. The same goes for the numbers — your total is your total, and
a reader must be able to tell at a glance which figures came from the service
and which from the desk.

The way to move the answer is to give the next fit what it lacked: the missing
history, the options that were declined, better features, or a different
`confidence_correction` chosen from the sweep. Not a number the fit never
produced.

### 8. Free-form `feedback` is the next iteration's to-do

When the response carries it, surface it and act on it — it is written to
improve the next request
([Free-form feedback](../../docs/02-endpoints.md#free-form-feedback)).

### 9. Self-check before the proposal goes out

- every recommended (key, qty) appears in the returned menu with `qty > 0`,
  at the size returned;
- no key appears twice;
- every line names the offer that will be executed, with the cost and terms
  that apply at that size;
- both kinds of refusal are listed — explicit zeros and absent keys;
- any portfolio figure is reproduced only when returned and described using
  the response's own profit basis; field names alone do not establish prediction
  provenance;
- the parse-report and calibration context are stated when the response carries them;
- every number that is yours is labelled as yours.

## A result that is not `done`

`failed` carries its class in `error_code` and `error`; a fit that failed
while grounding also carries the diagnosis written for the member in
`feedback` and the technical report in `feedback_report`
([When a fit fails](../../docs/02-endpoints.md#when-a-fit-fails)), and the
conditions behind cluster failures are tabulated in
[docs/04-errors-and-checks.md](../../docs/04-errors-and-checks.md#fit-time-failures).
Relay the diagnosis as written — there is no portfolio to interpret and
nothing to soften. `/predict` output is a payload
sanity check from a small reference model, **not** P34's answer, and a
`"mock": true` response carries deterministic placeholders rather than
predictions; neither belongs in a trade proposal. See
[p34-submit-and-monitor](../p34-submit-and-monitor/SKILL.md).
