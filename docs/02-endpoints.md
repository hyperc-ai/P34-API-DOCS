# 2. Endpoints, auth, and model versions

Base URL: **`https://api.hyperc.com/v1`**

## Authentication

Get an API key from the [management console](https://api.hyperc.com/app/)
(register → API keys). Send it on every request:

```
Authorization: Bearer <key>
```

Keys come in `test-…` and `profit-…` flavours tied to your plan; usage is
metered against your plan's compute budget over two rolling windows — weekly
and monthly (the console shows utilization of both in real time). Registration is free, but calling the API requires an **active
subscription** — requests on an account without one return `429` with
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
| `GET /result/{session_id}` | Poll the calculation: `queued` → `processing` → `done` / `failed`. `done` carries the predicted T=0 menu. |
| `POST /predict` | Instant selection from a small in-process reference model — a payload sanity-checker while the real calculation runs. **Not** P34's answer; `/result` is. |
| `DELETE /session/{id}` | Discard a session you no longer need. |
| `GET /queue` | Intake spool state (admin accounts). |

## Result statuses

| status | meaning |
| --- | --- |
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
  the request *would* have cost, with `"tokens_charged": 0`.
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

Every fit must resolve to a non-empty **business description**. `/fit`
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
`simulator_default`), and the resolved text is recorded with the fit task. Current model versions
do not consume it yet — the interface and the recording exist so the
description can later be used to **enrich the choices and balance risks**.

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

### Grounding modes (reserved)

`/fit` accepts an optional `grounding_mode` (also inside `market_type`; the
top-level field wins): `internal` — the default, today's server-side replay
grounding — or `business_led`, a **reserved** mode in which the recorded
business description and documents will drive the outcome reconstruction
instead of the fixed replay formula. `business_led` is disabled pending a
redesign of the grounding pipeline: requesting it returns **501**. Omit the
field (or send `internal`); the applied mode is echoed in the fit response's
`grounding_mode`.

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

An active subscription is required to call the API (see Authentication
above). Compute budgets scale with the plan — see the plans page in the
[management console](https://api.hyperc.com/app/). Accounts without an
active plan also have a request-size cap (currently 300 MB per request),
though their requests are refused with `429` regardless.
