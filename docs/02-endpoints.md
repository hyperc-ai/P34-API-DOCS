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
every month (2,000 tokens on the plan currently sold, **4,000 for founding members**),
**unused tokens accumulate**, and API calls debit the balance
(a weekly window remains as a burst bound only) — see
[the token wallet](06-token-wallet.md) for accrual, the founding grant,
transfers and the ledger. Registration is free, but calling the API requires tokens — an
account with no active subscription and an empty wallet gets `429` with
`"no active subscription — subscribe to a plan to use the API"`. Subscribe
from the console's plans page. `GET /` and `GET /health` are open liveness
endpoints. Exception: [mock requests](#mock-mode-free-integration-testing)
(`"mock": true`) are free and need only a registered key, so you can build
and test your integration before subscribing.

## Endpoints

| Method & path | Purpose |
| --- | --- |
| `GET /` | Service info: protocol, available model versions, endpoint list. |
| `GET /health` | Liveness probe. |
| `POST /fit` | Submit Menus + Sales + market_type (+ a resolvable [business description](#business-description)). Validates, grounds the history, enqueues the calculation. Returns `session_id` immediately. Add `"mock": true` for a free simulated run (see [Mock mode](#mock-mode-free-integration-testing)). |
| `GET /result/{session_id}` | Poll the calculation: `grounding` → `queued` → `processing` → `done` / `failed`. `done` carries the predicted T=0 menu. |
| `POST /predict` | Instant selection from a small in-process reference model — a payload sanity-checker while the real calculation runs. **Not** P34's answer; `/result` is. |
| `DELETE /session/{id}` | Discard a session you no longer need. |
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

## Mock mode (free integration testing)

Add `"mock": true` to a `/fit` request — top-level field or `"mock": true`
inside `market_type` — to run it as a **simulation**: the request goes through
the exact same validation as a real fit (sheet parsing, menu-0 rules,
grounding, model-version and confidence checks — every 422 behaves
identically), but **no calculation runs and no tokens are charged**. Use it to
verify your request format and exercise your polling/response handling before
spending compute budget.

- A registered API key is still required (`401` otherwise), but mock requests
  work **without an active subscription** and with an exhausted budget — you
  can finish and test your integration before subscribing.
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
- `"mock": "failed"` simulates a **failing** fit instead — `/result` ends at
  `status: "failed"` with an `error` field — so you can test your error path.
- `"mock_result_seconds": <n>` (default 6, max 600) sets how long the
  simulated calculation takes; `0` makes the terminal status available on the
  first poll. The first third of the interval reports `queued`, the rest
  `processing`.

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "mock": true, "mock_result_seconds": 30 }
```

Mock sessions don't appear in the console's calculations panel and are pruned
after 7 days (`DELETE /session/{id}` removes one immediately).

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
4. **simulator-style payloads only**: requests with the simple sample-sheet
   column setup (`synthetic_inventory` + `synthetic_full` grounding, at most
   a few feature columns — what the [market simulator](https://api.hyperc.com/sim/)
   and the synthetic examples emit) fall back to a built-in default
   description, so legacy simulator clients keep working. Real business
   integrations (richer features or `business_observed` grounding) are not
   exempted;
5. none of the above exists → the request is rejected with **422**.

The fit response reports which source was used in
`business_description_source` (`request` / `account_profile` / `last_sent` /
`simulator_default`), and the resolved text is recorded with the fit task.

Under the default [`business_led` grounding mode](#grounding-modes) this
description is **executable input, not metadata**: it is compiled into the
economics adapter that reconstructs your labels, so its accuracy directly
determines result quality. (Under legacy `internal` grounding it is only
recorded, and the fixed replay formula is used instead.)

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

### Grounding modes

`/fit` accepts an optional `grounding_mode` (also inside `market_type`; the
top-level field wins). It decides **how your history becomes the labelled
examples the model learns from** — the single biggest lever on result
quality.

| value | what it does | use it when |
| --- | --- | --- |
| *omitted* | **The default: `business_led`.** Description-driven grounding is what you get when you express no preference. | you have nothing special to say |
| `default` (or `auto`) | Identical to omitting it — whatever grounding this deployment considers best. Spells the intent out for readers of your code. | you prefer to be explicit |
| `business_led` | Pins description-driven grounding by name. | you want the request to fail loudly on a server that cannot do it, instead of quietly getting the fallback |
| `internal` | The original fixed replay formula: a synthetic-inventory economics model whose cost structure crosses the API as a handful of scalars. | simulator-style payloads and the quickstart |
| `client_grounded` | **You** ground the history. Every historical option row carrying a `profit` is published with that value verbatim; P34 derives nothing — no replay, no adapter, no LLM, no grounding charge. | your own systems already value the options you *did not* take |

> **Changed:** an omitted `grounding_mode` used to mean `internal`. It now
> means `business_led`. If you send no `grounding_mode` today, your fits
> become **asynchronous** (`status: "grounding"` — see
> [below](#it-runs-asynchronously)) and carry a
> [grounding charge](#what-it-costs). To keep the old behaviour exactly, send
> `"grounding_mode": "internal"` — the legacy path did not change, it just
> has to be asked for by name.

The applied mode is echoed back in the fit response's `grounding_mode`, and
it always names a concrete mode (`internal` / `business_led`) — never the
alias you sent. On a deployment that does not run the business-led pipeline,
omitting the field still resolves to `internal`, so nothing there changes.

One thing the new default *relaxes*: `/fit` refuses a history that is too
thin to fit ([volume floors](04-errors-and-checks.md#common-422-errors)), but
a business-led fit is only held to the structural checks — grounding is what
produces the rows the model trains on, so the intake counts are not the ones
it will see. Histories that a bare `internal` fit rejects at intake are
accepted here.

#### Why business-led grounding is recommended

`internal` can only express economics that fit its fixed formula. Real cost
structures — tiered and per-channel fees, accumulated and holding costs,
write-off schedules, minimum order quantities — have nowhere to go in it, so
they get approximated away, and the model learns from labels that do not
match your P&L.

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

#### What it costs

Grounding is metered and billed as its own line when the task is published —
the LLM work of compiling your adapter plus the CPU of the replay — and
appears in your [ledger](06-token-wallet.md) as a `service` entry. The fit's
own compute is billed separately at settlement, exactly as for `internal`. A
fit that fails during grounding is metered but **charged nothing**. Compiled
adapters are cached per account and description, so only the first fit after
you change your description pays the compile cost.

#### Bringing your own labels: `client_grounded`

Both modes above exist to **derive** a profit for every option row, and both
deliberately discard whatever `profit` you sent on the rows you did not choose
— they are about to recompute it. If your own systems already value the
options you declined, that rule is backwards: the labels are the input, not
something to be reconstructed.

`"grounding_mode": "client_grounded"` inverts it. Every historical option row
carrying a finite `profit` is published as a **labeled** row with that value
verbatim; every row without one is published as **unlabeled** context. No
replay, no compiled adapter, no LLM, no workspace VM, and no
[grounding charge](#what-it-costs). It is synchronous — `/fit` answers
`"status": "queued"` exactly as `internal` does.

One 48-row history (12 keys × 4 quantities), submitted three ways:

| you send | mode | `labeled_rows` | `unlabeled_rows` | what happened |
| --- | --- | ---: | ---: | --- |
| `profit` on all 48 rows | `client_grounded` | 48 | 0 | all 48 of your labels published as sent |
| `profit` on the 12 chosen rows only | `client_grounded` | 12 | 36 | the other 36 became unlabeled context |
| `profit` on all 48 rows | `internal` | 48 | 0 | your 36 non-chosen values were **discarded** and recomputed — `parse_report.profit_values_ignored_on_non_chosen` reads `36` |

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

`historically_chosen` keeps its usual job here: it marks the group's labeled
pick, and the quantity on that row is the reference every other option in the
group is compared against.

## Turning the plausibility checks off

`/fit` forms two different kinds of opinion about a submission.
**Structural** checks establish that the request can be fitted at all:
required columns present, T=0 rows agreeing with menu `0`, exactly one
`historically_chosen` row per group, frames that line up, train and eval
carrying the same feature columns. **Plausibility** checks are advisory
economics: the [volume floors](04-errors-and-checks.md#common-422-errors), the
`historically_available` / `historically_chosen` consistency pair, and the
replay-horizon bound on Sales.

`"checks": "off"` skips the **plausibility** checks only, in any grounding
mode. Like `grounding_mode`, it is accepted at the top level or inside
`market_type`, and the top-level field wins:

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "grounding_mode": "client_grounded", "checks": "off" }
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
the plan — 2,000 tokens a month on the plan currently sold, doubled to 4,000
for founding members —
see the plans page in the
[management console](https://api.hyperc.com/app/). Accounts without an
active plan also have a request-size cap (currently 300 MB per request);
with an empty wallet on top, their requests are refused with `429`.
