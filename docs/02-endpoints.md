# 2. Endpoints, auth, and model versions

Base URL: **`https://api.hyperc.com/v1`**

## Authentication

Get an API key from the [management console](https://api.hyperc.com/app/)
(register → API keys). Send it on every request:

```
Authorization: Bearer <key>
```

Keys come in `test-…` and `profit-…` flavours tied to your plan; usage is
metered against your plan's compute budget (the console shows utilization in
real time). Registration is free, but calling the API requires an **active
subscription** — requests on an account without one return `429` with
`"no active subscription — subscribe to a plan to use the API"`. Subscribe
from the console's plans page. `GET /` and `GET /health` are open liveness
endpoints.

## Endpoints

| Method & path | Purpose |
| --- | --- |
| `GET /` | Service info: protocol, available model versions, endpoint list. |
| `GET /health` | Liveness probe. |
| `POST /fit` | Submit Menus + Sales + market_type. Validates, grounds the history, enqueues the calculation. Returns `session_id` immediately. |
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
On `r007` the menu carries only the keys of the chosen market scenario's
solution rather than every key of your task menu — any key absent from the
response means "do not trade", exactly like a `qty: 0` row.

On `r006`+ fits the response also carries the **confidence sweep** (see
[Confidence correction](#confidence-correction)): for every candidate
correction on a grid (`-0.3 … +0.3`, step `0.05`, the applied value included
and flagged `"applied": true`), the threshold it produces and what would have
been selected — number of market scenarios passing, the winning scenario, its
selected-key count and total predicted profit. Use it to judge how sensitive
the portfolio is to the confidence setting and to pick a correction for the
next `/fit` without paying for exploratory runs. Absent on pre-`r006` model
versions.

On `r007` the sweep comes from the model itself and differs slightly: the
grid is fixed (`-0.3, -0.2, -0.1, -0.05, 0, +0.05, +0.1, +0.2, +0.3` — an
off-grid applied correction is not added as an extra entry), profits are
totals over the keys of the applied portfolio, and entries carry
`n_keys_positive` (keys with positive predicted profit under that correction)
instead of the per-scenario fields.

## Model versions

Every `/fit` runs against a released **model version**. Select one with the
optional top-level `model` field (or a `"model"` key inside `market_type`; the
top-level field wins):

```json
{ "menus": [...], "sales": [...], "market_type": {...}, "model": "r001" }
```

| version | meaning |
| --- | --- |
| `default` | the current live model revision (used when `model` is omitted) |
| `r000` | released tag with a dedicated universe-selector model |
| `r001` | the first released tag |
| `r003-alpha` | released tag with a pooled small-markets universe selector |
| `r003-alpha-ray` | same as `r003-alpha` with a distributed fitting backend (faster on large menus) |
| `r005` | released tag with a retrained universe selector and distributed fitting |
| `r006` | released tag with a **meta-calibrated** universe selector: the confidence threshold is chosen per prediction by a calibrator model and adjusted by `confidence_correction` |
| `r007` | released tag with an **improved meta-calibrated** selector: winner's-curse-aware scenario choice, a zero-inflation guard on the calibrated threshold, and reverse-market handling |

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
  "model": "r006", "confidence_correction": -0.1 }
```

Since `r006`, the model chooses its own selector confidence threshold per
prediction with a built-in **meta-calibrator**; you no longer set an absolute
level. `confidence_correction` is a small signed adjustment added on top of
the calibrated threshold — **positive values mean fewer, higher-confidence
selections; negative values admit more scenarios at the cost of confidence**.
Typical values are `+0.1` / `-0.1`. Out-of-range or non-numeric values are
rejected with 422. When omitted, the service default of **-0.1** applies.

On pre-`r006` model versions (which have no calibrator) the correction shifts
that version's fixed threshold default instead (`r005`: 0.6; earlier: 0.7).
The applied correction is fixed at fit time for the whole session — to compare
corrections, run one `/fit` per value.

The old absolute `confidence_level` parameter is retired: sending it (as a
field or inside `market_type`) returns 422 with a migration hint.

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
