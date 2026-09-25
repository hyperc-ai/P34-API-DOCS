# The history contract: integrity, completeness, and choice flags

Detail behind [SKILL.md](../SKILL.md). The column contract itself is
[docs/03-data-format.md](../../../docs/03-data-format.md); nothing here
repeats it.

## Source artifacts and provenance

The prepared tables are derived artifacts. The records they were derived from
are evidence, and evidence is immutable:

- keep every source file exactly as received, and keep enough identity to
  prove it did not change while you worked (checksum, size, export time);
- write the prepared tables to new files, and keep a mapping from each output
  column back to the source field and the formula that produced it;
- a required format change — renaming a column, splitting a compound field,
  converting a unit — still carries the source record through. Never describe
  the result as an observation that did not occur.

## Historical rows: retain, blank, do not invent

**Retain.** Every option that was on the table at a decision moment gets its
own row, at the granularity it was recorded, with the economics that applied
to it. That includes the options the business declined, the ones nobody has an
outcome for, and the ones that lost money. A history in which almost every
option was taken teaches "take everything" — see
[How much unlabeled context is enough](../../../docs/03-data-format.md#how-much-unlabeled-context-is-enough).

**Blank.** An outcome you do not know is a blank `profit`. `0` is a claim that
the option was taken and returned nothing, and the model will believe it.
Approximate values go in a named feature column instead, propagated to all
rows of the dataset.

**Multiple observed quantities.** For a historical offer with known results at
several quantities, follow [the maximum-observed-quantity rule](../../../docs/03-data-format.md#multiple-observed-quantities-for-one-historical-offer).
Send the maximum observed quantity and its known result, together with the
item's entire known cashflow history in Sales.

**Do not invent.** `historically_chosen` is a claim about what the business
actually did. Where there is no record, send no flag — the column is optional
and a group with no flag stays in the history. Do not present the reference
row the service fills in as the customer's past decision; it is a modelling
convention, not evidence. See
[What happens without it](../../../docs/03-data-format.md#what-happens-without-it).

## Transformations that are prohibited

Do not apply any transformation whose purpose is statistical compensation:

- outcome-selective removal (dropping losers, winners, or outliers by result);
- class balancing;
- over- or undersampling;
- duplicated or synthetic observations;
- invented labels;
- weights or feature columns whose purpose is to compensate for the observed
  sample distribution.

The reason is not squeamishness about statistics: P34 is pre-trained to work
on raw records, without loss weighting or compensation signals, and its
product is the *refusals* it learns from a faithfully unbalanced sample. A
compensated history describes a market that does not exist.

**What remains entirely fine:** ordinary formula columns; recorded cost, fee
and holding rates; faithful mapping into the contract's shape; and business
statistics such as a quantity-weighted average price. The test is purpose — a
column that encodes a business fact is a feature; the same column added to
offset how often an outcome appears in the sample is compensation.

**When asked for one:** decline it, say plainly which transformation you
declined and why, and offer the honest alternative — more recorded history,
more untaken options, better features, or a clearly separated sensitivity
analysis kept out of the fit input.

## Reducing a history window

A compute or budget limit may force a shorter history. That never authorises
silent data loss:

- keep **whole consecutive most-recent menus**, not a selection of rows or
  keys inside them — a menu is one decision moment and the model reads it as a
  complete option set;
- report the window kept, the decision moments dropped, and why;
- shortening the history is the supported way to make a dataset smaller;
  narrowing the live menu is not (see
  [Start small, iterate](../../../docs/03-data-format.md#start-small-iterate)).

## Derived option rows are not observations

The contract allows option rows whose outcome you calculated rather than
executed, marked with `historically_available = 0` — see
[Availability is not required on unlabeled rows](../../../docs/03-data-format.md#availability-is-not-required-on-unlabeled-rows).
These stay distinguishable from recorded history, keep their availability flag
and their provenance, and are never created to compensate for the sample. They
are optional: a correct first fit does not need any.

## The T=0 task menu: completeness

The task menu is what the model will choose from, so it has to be the real
choice set:

- **every currently executable quantity option per candidate**, with the cost
  and terms that actually apply — stock on hand, minimum order quantity, pack
  or lot increments, every tier and break price, and any stated business
  constraint. A schedule quoted as tiers or a step size has to be *expanded*
  into those rows: the quoted lines are prices, the rows are choices;
- options are mutually exclusive within a key-date, so alternative quantities
  and alternative supplier costs all belong in the same group — see
  [One choice per key-date](../../../docs/03-data-format.md#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive);
- **no pruning** for exceeding historical purchase sizes, for thin historical
  support, for looking unattractive under a client heuristic, or because the
  caller says they would not choose it. Report a historical-support limitation
  separately instead — name the options the history has never covered *and*
  say they remain on the menu, so the gap is a caveat on the reading rather
  than a silent deletion;
- no manufactured history to make an available quantity appear supported;
- `profit` blank on every T=0 row — the server rejects any value there;
- feasibility is a separate statement from forecast confidence. "We can order
  it" and "we expect it to sell" are two different columns of your report.

## What a completeness check can and cannot prove

A reader holding only the submitted rows cannot tell a complete option set
from a pruned one — nothing in the rows records what was left out. So:

- keep the **source availability schedule** with the submission, and keep a
  **coverage record** linking each feasible quantity and tier price in that
  schedule to the row that carries it;
- a check that has the schedule can report a real pass or a specific gap;
- a check without it reports **"cannot verify completeness"**. That is the
  honest result. A passing completeness claim made from the rows alone is
  false confidence, and it is exactly the claim a pruned submission would also
  produce.

## Cases with no supported answer

Report these explicitly instead of inventing a policy.

**Continuous or very large quantity spaces.** There is no published resolution
policy for a choice set that is a continuous range. Until one exists,
completeness for such a range **fails explicitly**. Do not replace the range
with quantiles or a sampled grid, and do not invent interval or range columns
the contract does not have. Two things — and only these two — can establish a
new completeness target: an authoritative published discretization policy, or
a caller-defined change to the actual business choice set with documented,
finite, legal options (a supplier that genuinely quotes in pallets). Approving
an arbitrary sample does not prove coverage of the original range; it changes
the question.

**A zero-quantity input row.** A zero in the *output* means the model declined
the deal. That does not imply a zero-`qty` *input* row. Input zero handling
follows the published contract; where it is ambiguous, ask rather than adding
a row on inference.

## Missing `historically_chosen`: what each mode does

`historically_chosen` is optional and stays optional. This table exists so you
can warn the caller about the consequences of its absence in the mode they are
about to use — not to turn it into a requirement, and never as a reason to
manufacture a flag. The modes are named in
[Grounding modes](../../../docs/02-endpoints.md#grounding-modes). Treat all of it as
the service's own processing: your job is to supply truthful records and the
facts it asks for.

| Mode / path | Consequence of a missing flag, and what to do |
| --- | --- |
| `business_led` (the default when `grounding_mode` is omitted) | Where a group carries no flag there is no executed batch to reason from, and how much of that group the service can label then turns on facts only you hold. Supply them in the business description: what stock was held, whether it sold out, and what your sales figures actually measure. Omitting them is what limits the labels you get back; manufacturing a flag is not the remedy. |
| `grounding_mode: "client_grounded"` | **Reserved for enterprise use after consultation with HyperC** to preserve private knowledge and know-how; correct client grounding requires vast compute resources. Use `business_led` for standard member/agent workflows. In an agreed integration, historical outcome values are yours and are published verbatim; the service derives nothing. The requirements that exist for replay — a Sales tape that reconciles, a replay horizon, a business description — do not apply here. Send `profit` on every historical option row you have valued and leave the rest blank; the blanks become the unlabeled context. See [Bringing your own labels](../../../docs/02-endpoints.md#bringing-your-own-labels-client_grounded). |

Check the response's echoed `grounding_mode`, `parse_report.historically_chosen`
and `parse_report.menus_groups_without_choice` against what you intended.
