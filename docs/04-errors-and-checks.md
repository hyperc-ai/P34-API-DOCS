# 4. Errors, fit-response fields, and quick self-checks

## Fit response fields

`POST /fit` returns immediately after grounding and enqueueing:

> Under the default [`business_led` grounding
> mode](02-endpoints.md#grounding-modes) grounding happens **after** the
> response, so `/fit` answers `"status": "grounding"` and the row-count
> fields below (`labeled_rows`, `unlabeled_rows`) arrive later — poll
> `/result` for them. Everything else on this page applies to both modes.

- `session_id` — use it to poll `/result`.
- `labeled_rows` / `unlabeled_rows` — sizes of the grounded context. A group
  counts as **labeled** when its chosen row carries a `profit` value (the
  observed-outcome marker; the value itself is replayed from Sales). Groups
  whose chosen row has no profit are the **unlabeled** context. If
  `labeled_rows` is 0, no historical group had a known outcome — check that
  chosen rows carry `profit` values. If `unlabeled_rows` is 0, every group you
  sent is observed — send the groups with no trustworthy outcome too
  ([data format](03-data-format.md#include-the-deals-you-did-not-take));
  current models refuse an all-observed history at fit time. **Read the ratio,
  not just the zero check:** an `unlabeled_rows` that is a thin slice of the
  total clears every gate and then trains a take-all policy — see [how much
  unlabeled context is
  enough](03-data-format.md#how-much-unlabeled-context-is-enough).
- `task_menu_rows` — how many T=0 option rows were received.
- `parse_report` — per-rule counts of dropped/ignored rows, and the only place
  the shrinkage is visible. A large `menus_rows_dropped_no_choice` means whole
  (menu, key) groups had no `historically_chosen = 1` row and were dropped in
  full — usually the column is missing, or it was filled as "what the business
  selected" and left blank wherever nobody selected anything. It marks the
  group's **labeled pick**, which every group needs; see [what it really
  means](03-data-format.md#what-historically_chosen-really-means). Each
  counter's exact granularity — row, cell, or whole group — is tabulated in
  [what intake drops](03-data-format.md#what-intake-drops-and-what-it-reports).
- `model` — the model version this fit will run on.
- `business_description_source` — where the fit's
  [business description](02-endpoints.md#business-description) came from:
  `request`, `account_profile` (console Business profile), `last_sent`
  (reused from the account's previous fit), or `simulator_default` (the
  built-in fallback for simulator-style payloads).
- `grounding_mode` — the applied
  [grounding mode](02-endpoints.md#grounding-modes): `business_led` (what an
  omitted field now means) or `internal` (asked for by name). Always a
  concrete mode, so this is where you confirm what an omitted field or a
  `default`/`auto` alias resolved to.

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
size cap; **501** — you asked for `business_led`
[grounding](02-endpoints.md#grounding-modes) on a deployment that does not
run that pipeline (send `default` instead and you get that server's best
available grounding rather than an error); **429** — no active subscription (subscribe in the console), or
the plan's compute budget is exhausted for the current weekly or monthly
window (see utilization in the
[management console](https://api.hyperc.com/app/)).

## Fit-time (cluster) failures

`POST /fit` validates shape, not statistics: a request can pass intake and
still fail when the calculation runs on the cluster. These surface as
`status: "failed"` on `GET /result/{session_id}`, with the reason in `error`:

| `error` contains | meaning | fix |
| --- | --- | --- |
| `Unlabeled business-menu mask selected zero rows` | the history contains only observed outcomes — no unlabeled context for the model to contrast against. P34 needs both halves of a [partially observed market](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement) | include the groups with no trustworthy outcome — one row flagged `historically_chosen`, `profit` blank on every row of the group — see [the data-format guide](03-data-format.md#include-the-deals-you-did-not-take) |
| `NotEnoughData: No qty values have at least 100 rows` | too little observed history — the model needs at least ~100 observed groups sharing a qty option (`max_qty_rows` in the message reports your best count) | send more history: more observed keys/menus per qty option |
| `Not enough valid menus to train on` | the history spans too few decision moments (`valid_fc_group_count` reports what survived; the floor is 10) | spread the history over more menus — at least ~10 decision moments, 50+ recommended |
| `No FC-fit universe had enough rows to fit an FC regressor` | every internal fit candidate was skipped — too few observed (outcome-carrying) deals per menu | send more observed deals per decision moment — aim for 20+ per menu |
| `bg_replay_ground: reconciliation failed` | replaying your Sales tape did not reproduce the `profit` you reported. Either the economics in your business description are wrong, **or** the tape and the profit were computed from different quantities (a rounded/aggregated/re-derived export) | read the stats in the message before changing anything — see [reading a reconciliation failure](#reading-a-reconciliation-failure) below |

### Reading a reconciliation failure

The message carries the whole diagnosis; read it before touching your model.

```
reconciliation failed: {'n_rows': 2526, 'n_excluded_nan': 0, 'n_compared': 2526,
 'n_within_zero_band': 2387, 'p80': 0.2449, 'p98': 1.0, 'median_signed': 0.0492}
```

- `n_within_zero_band` — rows that matched **exactly** (within 1% of the menu's
  mean `|profit|`). Here 2,387 of 2,526.
- `p80`/`p98` are percentiles of the relative difference over the **remaining**
  rows only — 139 of them above, not all 2,526. Gate: `p80 ≤ 0.10`,
  `p98 ≤ 0.30`. `p98 = 1.0` means at least one row has the opposite sign.
- `median_signed` is likewise over those remaining rows only. Positive = the
  replay reports **more** profit than your books.

So a small `p80` failure with a large `n_within_zero_band` does **not** mean
"the model is 24% wrong". It means most rows are perfect and a minority are not
— and *which* minority is the question worth answering. Group the disagreeing
rows by key, quantity and any regime flag you have: if they fall into an
identifiable subset and the errors run in both directions, suspect the tape,
not the formula — see
[The tape and the profit must agree](03-data-format.md#the-tape-and-the-profit-must-agree).
If instead the bias is one-signed across the board, a cost component is missing
or double-counted; `median_signed` gives you its sign and rough size.

Do not tune a fact-grounded component to make the gate pass. Undercharging one
term can partially cancel an unrelated error and *improve* the number while
making the model wrong — which then trains on the wrong economics.

A fit that fails on the cluster is metered but **charged nothing**, so these
cost you time rather than tokens. They still cost you a full queue wait, so
catching both conditions client-side before submitting (count your observed
groups per qty; make sure declined groups are present) is worth the few lines
of pandas.

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
