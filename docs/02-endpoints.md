# 2. Endpoints, auth, and model versions

Base URL: **`https://api.hyperc.com/v1`**

## Authentication

Get an API key from the [management console](https://api.hyperc.com/app/)
(register → API keys). A `test-` key is **issued automatically the moment
your subscription activates** — and if you use the agent-workspace VM, the
same key is placed on the machine as `/workspace/.p34_api_key`, so your agent
can call the API without any copy-pasting. Send it on every request:

```
Authorization: Bearer <key>
```

Keys come in `test-…` and `profit-…` flavours tied to your plan
(`profit-` keys are **not yet self-serve** — the console issues `test-` keys
only for now); usage is
metered against your **token wallet**: your plan's token amount is credited
every month (**doubled for founding members**),
**unused tokens accumulate**, and API calls debit the balance
(a weekly window remains as a burst bound only) — see
[the token wallet](06-token-wallet.md) for accrual, the founding grant,
transfers and the ledger. Registration is free, but calling the API requires tokens — an
account with no active subscription and an empty wallet gets `429` with
`"no active subscription — subscribe to a plan to use the API"`. Subscribe
from the console's plans page. `GET /` and `GET /health` are open liveness
endpoints. Exception: [input-test requests](#mock-mode-input-testing)
(`"mock": true`) work on every tier, including a free key testing a market
that is not available for an actual free fit. They parse and validate the
input without grounding, compute, or billing. Website workspaces also receive a
`free-` key for fits in select markets; see
[Free workspace fits](#free-workspace-fits).

## Endpoints

| Method & path | Purpose |
| --- | --- |
| `GET /` | Service info: protocol, available model versions, endpoint list. |
| `GET /health` | Liveness probe. |
| `POST /fit` | Submit Menus + Sales + market_type (+ a resolvable [business description](#business-description)). Validates, grounds the history, enqueues the calculation. Returns `session_id` immediately. Add `"mock": true` to test input parsing and validation only (see [Input-test mode](#mock-mode-input-testing)). |
| `GET /result/{session_id}` | Poll the calculation: `grounding` → `queued` → `processing` → `done` / `failed`. `done` carries the predicted T=0 menu. |
| `POST /predict` | Instant selection from a small in-process reference model — a payload sanity-checker while the real calculation runs. **Not** P34's answer; `/result` is. |
| `DELETE /session/{id}` | Cancel a running fit you own (a grounding-phase fit is aborted; a queued/processing calculation is canceled within about a minute) and discard the session. Response: `{"ok": true, "canceled": {"grounding": bool, "calculation": bool}}`. |
| `GET /queue` | Intake spool state (admin accounts). |
| `GET /account/balance` | Token wallet balance, monthly grant and founding status (accruals materialize on read). [Details.](06-token-wallet.md) |
| `GET /account/ledger` | Full query-able token ledger — every pay-in/pay-out with time, from, to, amount, msg; cursor-paginated. [Details.](06-token-wallet.md) |
| `POST /account/transfer` | Send tokens to another account by email. [Details.](06-token-wallet.md) |

## Result statuses

| status | meaning |
| --- | --- |
| `grounding` | your economics are being compiled from your business description and your history replayed through them — the phase a [business-led](#grounding-modes) fit (the default) starts in. Takes minutes. Ends by moving to `queued`, or to `failed` with a `feedback` field. |
| `queued` | waiting for the compute queue. |
| `processing` | fitting/predicting on the cluster (a `runner` field carries progress detail). |
| `done` | predictions ready — see below. |
| `failed` | something broke; `error` carries the reason. |
| 404 | unknown session id (wrong server, or the session was removed). |

A `done` response contains **only the T=0 menu, with profit predictions**:

```json
{
  "status": "done",
  "menu": [
    {"key": "A001", "menu": 0, "T": 0, "qty": 3.0, "profit": 42.7},
    {"key": "A002", "menu": 0, "T": 0, "qty": 0.0, "profit": -1.2}
  ],
  "n_selected": 1,
  "predicted_profit_sum": 42.7,
  "summary": { "...": "per-bag prediction summary" },
  "confidence_thresh_calibrated": 0.48,
  "confidence_correction": -0.1,
  "confidence_thresh_effective": 0.38,
  "confidence_sweep": [
    {"correction": -0.1, "threshold": 0.38, "n_multiverses": 12,
     "applied": true, "multiverse_index": 7, "n_selected_keys": 66,
     "total_predicted_profit": 205.7},
    {"correction": 0.0, "threshold": 0.48, "...": "one entry per correction"}
  ]
}
```

One row per key of your task menu: `qty` is the model-selected size (`0` = do
not trade) and `profit` the predicted total profit at that size. Keys are your
original ids. Take the `qty > 0` rows together as the recommended portfolio.
On `r008`, `rc012` and `rc012-ray` (and `default`, which aliases `rc012`) the
menu carries only the keys of the chosen market scenario's solution rather
than every key of your task menu — any key absent from the response means "do not trade",
exactly like a `qty: 0` row.

On `r008`, `rc012` and `rc012-ray` fits the response also carries the
**confidence sweep**
(see [Confidence correction](#confidence-correction)): for every candidate
correction on a fixed grid (`-0.3, -0.2, -0.1, -0.05, 0, +0.05, +0.1, +0.2,
+0.3`, the applied value flagged `"applied": true`; an off-grid applied
correction is not added as an extra entry), the threshold it produces,
`n_keys_positive` (keys with positive predicted profit under that correction)
and the total predicted profit over the keys of the applied portfolio. Use it
to judge how sensitive the portfolio is to the confidence setting and to pick
a correction for the next `/fit` without paying for exploratory runs. Absent
on `r003-alpha-ray`.

### Where feedback is delivered

A [business-led](#grounding-modes) fit produces process feedback while it
grounds: **channel entries** — blocking problems, defaulted assumptions,
interpretations — and one **final report** at the end. `/result` carries a
`feedback_delivery` block saying where the service is writing them in your
workspace and how far it got. It is served while the session is `grounding`,
when it `failed`, and on a published fit's `queued` / `processing` / `done`
polls:

```json
"feedback_delivery": {
  "target": "project",
  "project_id": "prj_0a1b2c3d4e5f",
  "run_id": "run_9f8e7d6c5b4a",
  "path": "/workspace/260908-demo",
  "delivered": 2,
  "pending": 1,
  "last_error": "GatewayError: append /workspace/260908-demo/ERROR.md: HTTP 502"
}
```

| field | meaning |
| --- | --- |
| `target` | `project` when the fit was [bound to a project](#binding-a-fit-to-a-workspace-project), `session` when it was not. |
| `project_id` / `run_id` | the bound pair; both `null` on a session-scoped fit. |
| `path` | where these entries belong (it names the destination whether or not anything has been written yet): the project folder, or `/workspace/api-feedback/<session_id>/`. An unbound session's `REPORT.md` sits **in** that folder; a bound run's sits one level below, under `runs/<run_id>/`. `null` if the destination could not be determined. |
| `delivered` / `pending` | how many entries have reached your workspace, and how many are still owed. |
| `last_error` | why the owed entries have not moved; `null` when nothing is outstanding. |

**How to read it.** Each poll re-attempts a few of the owed entries before
reporting these counts, so a `pending` that falls to `0` as you poll means
everything landed. A `pending` that does not fall is not a lost entry — it is
still held for you and still retried — and `last_error` says why it has not
moved: this account has no workspace to deliver to, or the workspace refused
the write or could not be reached. Redelivery is deduplicated on the entry's
own id, so a retry never doubles an entry that already arrived.

While the session is `grounding` or `failed`, the response also carries
`feedback_log`: a copy of the **channel** entries in the poll itself, so you
can read them without going to the workspace at all. It is a recent-history
window, not the archive — at most 50 entries, each body truncated to 2,000
characters — and it never contains the final report, which is written to your
workspace only. That is why a published fit's polls keep retrying delivery:
its report is produced after the task reaches the compute queue, and the
workspace is the only place it lands.

## Free workspace fits

A website workspace's `free-` key can submit actual fits for markets supported by the free tier,
without activating a full VM. Send the normal
`/fit` request,
with `grounding_mode: "business_led"` and the market identified in this request's
`business_description`. **Omit `mock`**, including inside `market_type`.
An actual free-key fit for a market outside the supported set is refused
with HTTP 403,
`code: "free_markets_only"`, and the exact message `free tier only supports
select markets, including t5market.com.` The eligibility rule in this section
and the API's returned error are the canonical public contract. A separate
`mock: true` input test still works for that payload, but does not
make a later actual fit eligible.

Free and paid business-led clients use the same endpoints, input menu format,
session/request/task identifiers, asynchronous acknowledgement and result-polling
workflow. A free fit acknowledges `status: "grounding"` before preparing its
answer; poll until `done` or `failed` and read the same output menu fields.
Retries may return the existing session with `replayed: true`.

Free-tier results are portfolios returned through the normal fit/result workflow.
Interpret the fields and provenance the response supplies; do not invent missing
prediction, training, calibration, or model provenance. `mock: true` results
below are placeholders
from a separate input-test attempt.

A nonzero portfolio can be submitted to the named market under
its validity, account, funding and authorization rules. The API does not place
an order. An all-zero menu means no trade; a failed or expired result must not be
submitted as a new order.

## Mock mode: input testing

Add `"mock": true` to a `/fit` request — top-level field or `"mock": true`
inside `market_type` — to test fit input parsing and validation before a
separate real fit or prediction. The service performs no grounding, compute,
or billing. It can therefore catch structural input errors, but it does not
prove that grounding or a real fit will succeed.

- An API key is still required (`401` otherwise). Input tests work on every
  tier, without an active subscription and with an exhausted budget. This
  includes a free key testing a market outside the free-tier supported set.
- `/result` plays the real lifecycle (`queued` → `processing` → `done`) on a
  short timer, and the `done` payload has the full real shape shown above —
  `menu`, `n_selected`, `predicted_profit_sum`, `summary`, and the
  `confidence_*` / `confidence_sweep` fields on sweep-capable model versions.
  The numbers are **deterministic placeholders derived from your own T=0
  menu, not predictions**; every mock response carries `"mock": true` and a
  `mock_note` so it can never be mistaken for a real result.
- The fit response's `billing` block reports the `input_cells` and `effort`
  the request *would* have cost, with `"tokens_charged": 0` (and
  `"tokens_charged_units": 0`).

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "mock": true, "mock_result_seconds": 30 }
```

Mock sessions don't appear in the console's calculations panel and are pruned
after 7 days (`DELETE /session/{id}` removes one immediately; on a real
session the same call cancels the fit — see the endpoint table).

## Model versions

Every `/fit` runs against a released **model version**. Select one with the
optional top-level `model` field (or a `"model"` key inside `market_type`; the
top-level field wins):

```json
{ "menus": [...], "sales": [...], "market_type": {...}, "model": "r008" }
```

| version | meaning |
| --- | --- |
| `default` | alias for the current recommended model (used when `model` is omitted) — currently `rc012` |
| `r003-alpha-ray` | released tag with a pooled small-markets universe selector and a distributed fitting backend (faster on large menus) |
| `r008` | released tag with a meta-calibrated universe selector, a `predict_proba` correctness fix in the selector path, and a selector retrained on the full 29-market r008 telemetry sweep |
| `rc012` | release candidate built on the `r008` line: multiverse candidates are chosen for **variety** across ten quality metrics instead of by a pareto front, and selector thresholding is **target-calibrated** — a zero-take classifier gates predictions and a fixed calibrated threshold replaces the per-prediction threshold regression; ships a selector retrained on an updated confidence-feature set |
| `rc012-ray` | release candidate: `rc012`'s selection and target-calibrated thresholding on a **ray-distributed fitting backend** — the phase-1 fit and candidate fitting fan out over the compute cluster, which is faster on large menus; predictions use the same selector as `rc012` |

`GET /` lists the versions the server currently offers; an unknown version is
rejected with 422. The chosen version is echoed in the `/fit` response and in
`/result`'s `runner` detail; the whole calculation — fit **and** predict —
executes from that version.

## Confidence correction

`/fit` accepts an optional `confidence_correction` (number in `[-1, 1]`; also
accepted as a `"confidence_correction"` key inside `market_type`, the
top-level field wins):

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "model": "rc012", "confidence_correction": -0.1 }
```

On `r008`, `rc012` and `rc012-ray`, the model chooses its own selector confidence threshold per
prediction with a built-in **meta-calibrator**; you no longer set an absolute
level. `confidence_correction` is a small signed adjustment added on top of
the calibrated threshold — **positive values mean fewer, higher-confidence
selections; negative values admit more scenarios at the cost of confidence**.
Typical values are `+0.1` / `-0.1`. Out-of-range or non-numeric values are
rejected with 422. When omitted, the service default is **`0.0`** (no
adjustment) on `default`, `r008`, `rc012` and `rc012-ray`, whose selectors are
retrained on their own telemetry sweeps and whose calibrated thresholds are
used as-is.

On `r003-alpha-ray` (which predates the calibrator) the correction shifts the
fixed threshold default `0.7` instead.
The applied correction is fixed at fit time for the whole session — to compare
corrections, run one `/fit` per value.

The old absolute `confidence_level` parameter is retired: sending it (as a
field or inside `market_type`) returns 422 with a migration hint.

## Business description

Every fit must resolve to a non-empty **business description** — except a
[`client_grounded`](#bringing-your-own-labels-client_grounded) one, which
compiles nothing from it and so does not require it. `/fit`
accepts an optional top-level `business_description` string (also accepted
inside `market_type`; the top-level field wins):

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "business_description": "Wholesale reseller of industrial fasteners on ..." }
```

Resolution order when the field is absent or empty:

1. the `business_description` sent in the request;
2. the description saved in the [management console](https://api.hyperc.com/app/)
   dashboard (**Business profile → Business description**);
3. the description this account **last sent** on a previous `/fit` (the
   service records it every time one is sent — mock fits included);
4. none of the above exists → the request is rejected with **422**.

The fit response reports which source was used in
`business_description_source` (`request` / `account_profile` / `last_sent`),
and the resolved text is recorded with the fit task.

Under the default [`business_led` grounding mode](#grounding-modes) this
description is **executable input, not metadata**: it is compiled into the
economics adapter that reconstructs your labels, so its accuracy directly
determines result quality.

Note that step 2 makes the console description a first-class way to drive
fits: save it once in the dashboard, then send `/fit` requests with **no**
`business_description` field at all and `"grounding_mode": "default"`. The
response's `business_description_source` will read `account_profile`, and the
saved text is what your grounding is compiled from. This keeps a long,
carefully-maintained description out of every request payload — and lets a
non-engineer own it in the console while the integration stays untouched.

### What to write in it

Along with the actual description of the business (what is traded, on which
market, at what decision cadence), you **must provide all necessary details
about how the unit economics is computed**: all the fees, accumulated costs,
holding costs, and so on — with approximations where necessary. Start with
formula-based approximations of the cost structure per deal/item/asset and
deepen them over iterations (see
[Start small, iterate](03-data-format.md#start-small-iterate)).

**If an agent is assembling the API input**, the agent must either ask the
user to provide this unit-economics information, or research it on the
internet with the maximum effort possible — it is later used to enrich the
choices and balance risks, so a thin description degrades the result.

### Fix the profit window and write-off mechanics

Profit is meaningful over a stated business time frame. Before calculating
labels or submitting a fit, fix the economic write-off cutoff and describe it
in `business_description`; do not let the available export window silently
choose it. State:

- the duration in calendar units and in the tables' `T` units, its starting
  event (decision, purchase, receipt, or settlement), and whether the cutoff
  includes events exactly on the boundary; explain how `T_lead` affects it;
- what happens to every leftover, unsold or non-liquidated position at that
  cutoff: full write-off, a specified percentage write-off, or liquidation;
- for a percentage, its exact base (for example, remaining units × landed
  unit cost), the residual value retained, and any liquidation, disposal,
  holding or financing costs; state whether residual value is cash recovered
  or an accounting valuation;
- how later sales, returns and recoveries are treated, and how you handle
  positions whose observation window has not yet reached the cutoff. An
  incomplete window is not evidence of zero sales through the full horizon.

Use formulas and actual business terms. For example, with purchase cost
already deducted, `profit = net sale proceeds through cutoff − total purchase
cost − holding costs + residual value − disposal costs`. A 100% write-off
sets residual value to zero; a 30% write-off of the remaining landed cost
retains 70% of that cost as residual value. Do not subtract the purchase cost
and then subtract that same written-off cost again. These are illustrations,
not default rates or a universal accounting policy.

The user-side agent should implement this deterministic calculation for the
recorded outcomes it can support, and preserve the rule, inputs, cutoff and
calculation with the request so it can be replayed. The same inputs and policy
must give the same result. This is ordinary business arithmetic; it does not
require the caller to build the service's counterfactual grounding engine.
Business-led grounding uses the description (and available workspace economics
code) to replay the history. Missing future observations must not be invented
to make a completed-horizon label. Keep estimates distinct from observations.

### Describe every submitted column

Include a data dictionary in `business_description` covering **every column
in each submitted table**, including standard columns and custom features.
For each, give its exact table and column name, business meaning, unit and
currency, type or encoding, and the meaning of blanks and zero. Add applicable
formulas, source/provenance, aggregation window, timestamps/timezone, reporting
delay, and when the value was knowable. Explain identifiers and join keys,
percentage scales, and whether a value is measured, calculated or estimated.
Column names alone are not a definition; a private file or link alone is not
a substitute for sending the meanings to the API.

For example: `Menus.unit_cost: USD per individual unit, landed purchase cost
including inbound freight, from the supplier invoice; blank means unknown`.
Describe `Sales.qty` separately from `Menus.qty`, and document each feature's
formula and lookback window. Keep the dictionary, tables and economics code
consistent when a column or policy changes.

These are preparation recommendations for reproducible economics, not new
wire fields or extra intake validation. Under `client_grounded`, the API still
accepts caller-supplied labels without a description or service-side replay;
keeping the same policy and dictionary is recommended for auditing those labels.

### Describe the quantity decision

State what one `qty` unit represents, the available size range, and how total
profit depends on size. Single-quantity offers will not pass a fit: formulate
at least three distinct, meaningful sizes per offer, with more where the
business supports them. Explain the money quantum for lending/bids or the
historical similarity and package rules for domain buckets. Follow the
[quantity formulation guide](03-data-format.md#multiple-quantity-choices-are-required);
do not fabricate historical outcomes to fill the alternatives.

### Grounding modes

`/fit` accepts an optional `grounding_mode` (also inside `market_type`; the
top-level field wins). It decides **how your history becomes the labelled
examples the model learns from** — the single biggest lever on result
quality.

**Use `business_led` for standard member and agent workflows.** Client-side
grounding is reserved for enterprise use after consultation with HyperC;
do not select it simply because you already have profit numbers. See the
[enterprise guidance below](#bringing-your-own-labels-client_grounded).

| value | what it does | use it when |
| --- | --- | --- |
| *omitted* | **The default: `business_led`.** Description-driven grounding is what you get when you express no preference. | you have nothing special to say |
| `default` (or `auto`) | Identical to omitting it: `business_led`. Spells the intent out for readers of your code. | you prefer to be explicit |
| `business_led` | Pins description-driven grounding by name. If that execution path is unavailable, the request fails. | you want to name the mode explicitly |
| `client_grounded` | **You** ground the history. Every historical option row carrying a `profit` is published with that value verbatim; P34 derives nothing — no replay, no adapter, no LLM, no grounding charge. | enterprise use agreed with HyperC after consultation, to preserve private knowledge and know-how; requires vast client-side compute resources |

> **Changed:** the legacy `internal` mode is retired. If you send no
> `grounding_mode` today, your fits use `business_led` and
> become **asynchronous** (`status: "grounding"` — see
> [below](#it-runs-asynchronously)) and carry a
> [grounding charge](#what-it-costs). Keep `business_led` unless HyperC has
> agreed an enterprise client-grounding integration after consultation.

The applied mode is echoed back in the fit response's `grounding_mode`, and
it always names a concrete mode — never the alias you sent.

One thing the new default *relaxes*: `/fit` refuses a history that is too
thin to fit ([volume floors](04-errors-and-checks.md#common-422-errors)), but
a business-led fit is only held to the structural checks — grounding is what
produces the rows the model trains on, so the intake counts are not the ones
it will see.

#### Why business-led grounding is recommended

Business-led grounding instead **compiles your
[business description](#business-description) into an economics adapter for
your account** (and, where your account has a workspace VM, reads your own
profit-calculation code from it). Your history is expanded into a grounded
option grid and replayed through *your* economics to produce the labels. The
replayed profits are then reconciled against the realized profits you sent:
if they disagree beyond tolerance the fit fails with feedback naming the
mismatch, instead of quietly training on wrong labels.

This is also why the description is worth real effort — see
[what to write in it](#what-to-write-in-it). It is no longer metadata; it is
the specification the grounding is compiled from.

#### It runs asynchronously

A business-led `/fit` returns **`"status": "grounding"`** immediately with
your `session_id` — compiling and replaying takes minutes, not milliseconds.
Poll `GET /result/{session_id}` exactly as you already do: it reports the
grounding phase while the pipeline runs, then switches to the normal
`queued` → `processing` → `done` lifecycle once the task reaches the compute
queue. A client that already polls through to `done` needs no changes.

If grounding cannot succeed, `/result` ends at `status: "failed"` with a
`feedback` field describing what to fix in your data or your description —
see [free-form feedback](#free-form-feedback).

#### Reusing grounding code

Business-led grounding automatically reuses validated Python code from a prior
successful fit **on the same account** when both of these match:

- The business description is exactly identical, including whitespace.
- The parsed data schema is unchanged: column names, data types, optional tables
  and market configuration. Row values and row counts may change.

A cache hit runs the saved optimized adapter, when available, without launching
agentic/Claude grounding or compiling it again. It still validates the code
against the new submission, expands options, safely replays profits and builds
features from the **current data**. Previous training rows, labels and predictions
are not reused. The subsequent P34 model fit still runs normally.

If saved code is unavailable, invalid, or fails validation/execution on the new
input before publication, the service falls back to full agentic grounding.
Schema, description or relevant runtime changes can require grounding again.
A cache hit is an optimization, not a guarantee of latency or a free model run.

No additional request field is required. Keep the description stable when the
business rules are unchanged; update it when the economics change. For example,
new sales records with the same columns and data types can reuse grounding code,
while changing a fee in the market configuration requires another grounding pass.

The submission acknowledgement exposes `grounding_cache_hit: true`,
`orchestration_mode: "code_cache"` and initial `phase: "cache_queued"` on a hit.
Continue polling the same `session_id` through `grounding`, `queued`, `processing`
and a terminal result. Treat `phase` as informational; it can change if the
pipeline falls back to agentic grounding. Acknowledged cache selection does not
mean the remaining validation or model work has already succeeded.

#### What it costs

Grounding is metered and billed as its own line when the task is published —
the LLM work of compiling your adapter plus the CPU of the replay — and
appears in your [ledger](06-token-wallet.md) as a `service` entry. The fit's
own compute is billed separately at settlement. A
fit can incur metered grounding work even if grounding fails. A successful
[grounding code cache hit](#reusing-grounding-code) avoids agentic compilation
work, but fresh-data validation/replay and the model's compute still incur their
normal metered charges. If cached execution falls back to agentic grounding,
that work is metered too; do not assume every repeat request has zero grounding
cost.

#### Bringing your own labels: `client_grounded`

**Enterprise use only — consult HyperC before implementing or selecting this
mode.** Correct client-side grounding requires **vast compute resources** and
is reserved for enterprise clients that need to preserve **private knowledge
and know-how** in their own grounding environment. Members and agents should
use the default `business_led` mode unless an enterprise integration has been
agreed with HyperC. If consultation has not happened, request it before
proceeding with client grounding.

Client-led/client-side grounding is described here using the documented API
value `client_grounded`; this guidance does not introduce a `client_led` API
value. Having recorded profits, a spreadsheet, or an inexpensive local profit
calculation does not establish a correct client grounding pipeline. Ordinary
calculation of recorded business outcomes remains part of preparing inputs
for `business_led`.

The absence of a service-side grounding charge does not remove the client's
compute burden. Do not use this mode as a shortcut around grounding cost,
latency, or reconciliation failures. Consultation should establish the private
knowledge requirements, compute capacity, and validation of the client-produced
labels. The technical contract below is retained for those enterprise
integrations; these usage restrictions are guidance, not a claim that the API
currently enforces enterprise access.

Business-led grounding exists to **derive** a profit for every option row and
deliberately discards whatever `profit` you sent on the rows you did not choose
— they are about to recompute it. In an agreed enterprise client-grounding
integration, the client's validated option values instead become the input.

`"grounding_mode": "client_grounded"` inverts it. Every historical option row
carrying a finite `profit` is published as a **labeled** row with that value
verbatim; every row without one is published as **unlabeled** context. No
replay, no compiled adapter, no LLM, no workspace VM, and no
[grounding charge](#what-it-costs). It is synchronous — `/fit` answers
`"status": "queued"` directly.

One 48-row history (12 keys × 4 quantities), submitted two ways:

| you send | mode | `labeled_rows` | `unlabeled_rows` | what happened |
| --- | --- | ---: | ---: | --- |
| `profit` on all 48 rows | `client_grounded` | 48 | 0 | all 48 of your labels published as sent |
| `profit` on the 12 rows the desk took only | `client_grounded` | 12 | 36 | the other 36 became unlabeled context |

`parse_report.client_labeled_rows` counts the labels this mode accepted. It is
the field to assert on in CI: if it is lower than you expect, some rows you
believe you labeled arrived with a blank or non-numeric `profit`.

**What it requires, and what it stops requiring.** At least one historical row
must carry a `profit` — publishing your labels is the whole mode, so there has
to be one, and a history with none is a 422. In exchange two things become
optional: the [business description](#business-description) (nothing is
compiled from it) and `market_type.parameters` (nothing is replayed, so there
is no replay horizon to describe).

**The trust boundary moves to you.** The derived modes replay your Sales tape
and reconcile it against the profits you reported, failing loudly when the two
disagree. This mode has nothing to reconcile against — whatever you send is
what the model learns. Two consequences worth designing for:

- **Blank is not zero.** A row with no `profit` is unlabeled context, and P34
  never coerces it to `0`. A zero would teach the model that a zero-profit
  option was actually observed, which is a different and much more damaging
  claim than "we do not know".
- **The [observed / unobserved split](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement)
  is now yours to get right.** Labeling every row you send leaves the model no
  declined options to contrast against, and the cluster refuses the fit with
  `Unlabeled business-menu mask selected zero rows`. Send the options you
  could not value, with `profit` blank.

`historically_chosen` keeps its usual job here, and stays optional: sent, it
marks the option your business actually took, and the quantity on that row is
the reference every other option in the group is compared against; absent, the
reference becomes the smallest available quantity among the rows you labeled,
filled in when the datasets are formed — see [Your previous business
policy](03-data-format.md#your-previous-business-policy-what-historically_chosen-marks).

## Turning the plausibility checks off

`/fit` forms two different kinds of opinion about a submission.
**Structural** checks establish that the request can be fitted at all:
required columns present, T=0 rows agreeing with menu `0`, at most one
`historically_chosen` row per group, any additional choice requirements
documented for the selected market, frames that line up, and train and eval
carrying the same feature columns. **Plausibility** checks are advisory
economics: the [volume floors](04-errors-and-checks.md#common-422-errors), the
`historically_available` / `historically_chosen` consistency pair, and the
replay-horizon bound on Sales.

`"checks": "off"` skips the **plausibility** checks only, in any grounding
mode. Like `grounding_mode`, it is accepted at the top level or inside
`market_type`, and the top-level field wins:

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "business_description": "...", "checks": "off" }
```

It **cannot** skip a structural check. Those exist because the cluster runner
raises `KeyError` or silently mis-fits without them, so turning one off would
trade a clear 422 at intake for an opaque failure hours later, on compute you
have already paid for. Nor does it lift the two safety refusals — a `profit`
on a T=0 row, and Sales dated after now — which protect the integrity of the
prediction rather than your convenience. Both are still 422 with
`"checks": "off"`.

Reach for it when you know your data is right and P34's generic opinions about
it are not: a market whose real order volumes sit below the floors, or an
availability convention that does not match the one the consistency check
assumes. Accepted values are `"on"` (the default) and `"off"`; anything else
is a 422 rather than a silent default.

Every fit records which way the switch was set — in `parse_report.checks` and
in the published task's metadata — so a fit that ran unchecked always says so.
With the checks off, `parse_report` also carries no `volume_warnings` key,
because nothing computed them.

## Binding a fit to a workspace project

If you drive the API from a HyperC agent workspace, `/fit` accepts an optional
top-level `workspace_context` naming the project and the run this submission
belongs to:

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "workspace_context": {"project_id": "prj_0a1b2c3d4e5f",
                        "run_id": "run_9f8e7d6c5b4a"} }
```

Both ids are issued by your own workspace — a **project** is the folder it
created for one task, a **run** is one submission attempt within that project —
and they are resolved through **your** workspace and nothing else. Sending them
binds this fit's process feedback to that project: the service appends its
entries to `ERROR.md`, `DISAMBIGUATION.md` and `THINKING.md` in the project
folder, and writes that run's `REPORT.md` under `runs/<run_id>/`, next to the
files you are already working in.

Without the field nothing changes: the feedback stays scoped to the API session
that produced it — returned in every `/result` poll as before and, when your
account has a workspace, also written to
`/workspace/api-feedback/<session_id>/`. There is no shared or global feedback
directory in either case. Either way,
[`feedback_delivery`](#where-feedback-is-delivered) on `/result` reports where
the entries went.

Entries from every run of a project share those three channel files, so each
one carries its own attribution line and a reader can tell this run's error
from an older run's:

```
## [2026-09-08 14:02 UTC] <title>
<!-- event:<event_id> project:<project_id> run:<run_id> session:<session_id> producer:<producer> -->

<body>
```

The `event:` marker is also how a redelivery is recognised, so an entry that
already arrived is never appended twice.

The binding is validated **before the request is spooled or billed**: a
`workspace_context` that cannot be resolved is a 422 whose `detail` starts
`workspace_context: ` (the reasons are listed under
[`workspace_context` refusals](04-errors-and-checks.md#workspace_context-refusals)),
and the fit costs you nothing. An id from another account's workspace is not
"forbidden", it is simply not registered in yours, so a refusal tells you
nothing about any other account. The acceptance response echoes the
**validated** pair back as `workspace_context`, together with the resulting
`feedback_target` (`"project"` when the fit is bound, `"session"` when it is
not).

A mock or `client_grounded` fit echoes those two fields back so
you can verify your integration, but produces no process feedback and so
delivers nothing: only a [business-led](#grounding-modes) fit has a grounding
phase to report on, and only it keeps the binding and retries delivery.

## Free-form feedback

Beyond the structured counters (`parse_report`, volume-floor errors), the API
may occasionally produce **rich free-form text feedback** about your input.
Agentic clients should surface it — and act on it: it is written to improve
the next iteration of your input construction (features to add, grounding to
fix, history to extend).

## Wire formats

Tables travel either as **JSON lists of records** (easy from CSV) or as
**base64-encoded Parquet** (dtype-exact). The sample client's
[`wire.py`](../examples/client/wire.py) has both helpers. Responses that carry
tables (e.g. `/predict`'s `selection`) use the same encoding.

## Request limits

Calling the API requires tokens in the wallet (see Authentication above and
[the token wallet](06-token-wallet.md)). Monthly token accruals scale with
the plan and are doubled for founding members; the current amounts are on
the plans page in the
[management console](https://api.hyperc.com/app/). Accounts without an
active plan also have a request-size cap (currently 300 MB per request);
with an empty wallet on top, their requests are refused with `429`.
