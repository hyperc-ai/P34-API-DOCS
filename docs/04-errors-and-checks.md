# 4. Errors, fit-response fields, and quick self-checks

## Fit response fields

`POST /fit` returns immediately after grounding and enqueueing:

- `session_id` — use it to poll `/result`.
- `labeled_rows` / `unlabeled_rows` — sizes of the grounded context. A group
  counts as **labeled** when its chosen row carries a `profit` value (the
  observed-outcome marker; the value itself is replayed from Sales). Groups
  whose chosen row has no profit are the **unlabeled** context. If
  `labeled_rows` is 0, no historical group had an observed outcome — check
  that chosen rows carry `profit` values. If `unlabeled_rows` is 0, the
  history is all wins — include the deals you declined
  ([data format](03-data-format.md#include-the-deals-you-did-not-take));
  current models refuse an all-observed history at fit time.
- `task_menu_rows` — how many T=0 option rows were received.
- `parse_report` — per-rule counts of dropped/ignored rows. A large
  `menus_rows_dropped_no_choice` usually means `historically_chosen` is
  missing or mis-filled.
- `model` — the model version this fit will run on.
- `business_description_source` — where the fit's
  [business description](02-endpoints.md#business-description) came from:
  `request`, `account_profile` (console Business profile), `last_sent`
  (reused from the account's previous fit), or `simulator_default` (the
  built-in fallback for simulator-style payloads).
- `grounding_mode` — the applied
  [grounding mode](02-endpoints.md#grounding-modes-reserved); currently
  always `internal`.

## Common 422 errors

| message contains | fix |
| --- | --- |
| `menu 0 is reserved for the task` | move historical rows off menu 0. |
| `T=0 task rows must use the reserved menu id 0` | set `menu = 0` on the task rows. |
| `no menu-0 (T=0) task rows` | include the current menu you want predicted. |
| `dated after now (T > 0)` | your Sales contain future rows — trim to history. |
| `outside the replay horizon` | a sale is dated more than `inventory_holding_weeks_before_writeoff` after its menu (or before it). |
| `keys appear in historical menus at multiple T values` | split those into distinct keys or separate requests. |
| `grounding failed: ...` | economics couldn't replay — the message names the failing constraint (e.g. non-integer sales qty). |
| unknown `model` version | check `GET /` for the versions this server offers. |
| `business_description could not be resolved` | none of the three sources exists: send `business_description` in the request (the business **and** its unit economics — fees, accumulated/holding costs, approximations OK), or save one in the console's Business profile — see [Business description](02-endpoints.md#business-description). |

Other statuses you may meet: **401/403** — missing/invalid API key, or a
feature your account isn't flagged for; **413** — request over your plan's
size cap; **501** — you requested the reserved `business_led`
[grounding mode](02-endpoints.md#grounding-modes-reserved), which is
disabled pending redesign; **429** — no active subscription (subscribe in the console), or
the plan's compute budget is exhausted for the current weekly or monthly
window (see utilization in the
[management console](https://api.hyperc.com/app/)).

## Fit-time (cluster) failures

`POST /fit` validates shape, not statistics: a request can pass intake and
still fail when the calculation runs on the cluster. These surface as
`status: "failed"` on `GET /result/{session_id}`, with the reason in `error`:

| `error` contains | meaning | fix |
| --- | --- | --- |
| `Unlabeled business-menu mask selected zero rows` | the history contains only observed outcomes — no unlabeled context for the model to fit against | include the deals you declined: their menu groups with the would-be size flagged `historically_chosen` and `profit` blank on every row — see [the data-format guide](03-data-format.md#include-the-deals-you-did-not-take) |
| `NotEnoughData: No qty values have at least 100 rows` | too little observed history — the model needs at least ~100 observed groups sharing a qty option (`max_qty_rows` in the message reports your best count) | send more history: more observed keys/menus per qty option |
| `Not enough valid menus to train on` | the history spans too few decision moments (`valid_fc_group_count` reports what survived; the floor is 10) | spread the history over more menus — at least ~10 decision moments, 50+ recommended |
| `No FC-fit universe had enough rows to fit an FC regressor` | every internal fit candidate was skipped — too few observed (outcome-carrying) deals per menu | send more observed deals per decision moment — aim for 20+ per menu |

The session is billed at intake, so catching both conditions client-side
before submitting (count your observed groups per qty; make sure declined
groups are present) is worth the few lines of pandas.

## Quick self-checks before you file a support request

1. `GET https://api.hyperc.com/v1/health` — is the service up?
2. `POST /predict` with your `session_id` and your T=0 menu — the instant
   reference model checks that your payload parses and your columns make
   sense, without waiting for the cluster.
3. Re-read `parse_report` — most "why is my context so small" questions are
   answered by its drop counters.
4. Session looks stuck in `processing`? Large fits can legitimately run tens
   of minutes; the console's session view shows live progress. Cancel from
   the console if needed.
5. The pytest workflow in
   [`examples/pytest/`](../examples/pytest/) automates 1–3; run it with your
   key in CI so integration regressions surface before your traders do.
