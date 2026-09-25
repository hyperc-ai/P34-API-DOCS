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
  counts as **labeled** when a known `profit` marks it — on its
  `historically_chosen` row where you sent the flag, on any row where you did
  not (the value itself is replayed from Sales). Groups with no known profit
  are the **unlabeled** context. If `labeled_rows` is 0, no historical group
  had a known outcome — check that the rows you know the outcome for carry
  `profit` values. If `unlabeled_rows` is 0, every group you
  sent is observed — send the groups with no trustworthy outcome too
  ([data format](03-data-format.md#include-the-deals-you-did-not-take));
  current models refuse an all-observed history at fit time. **Read the ratio,
  not just the zero check:** an `unlabeled_rows` that is a thin slice of the
  total clears every gate and then trains a take-all policy — see [how much
  unlabeled context is
  enough](03-data-format.md#how-much-unlabeled-context-is-enough).
  Under [`client_grounded`](02-endpoints.md#bringing-your-own-labels-client_grounded)
  this counts **rows, not groups**, and the value *is* trusted: every
  historical row you sent a finite `profit` on is labeled, every other row is
  unlabeled context.
- `task_menu_rows` — how many T=0 option rows were received.
- `parse_report` — per-rule counts of dropped/ignored rows, and the only place
  the shrinkage is visible. It also records how the business's previous
  policy was read: `historically_chosen` is `"provided"` or `"absent"`, and
  `menus_groups_without_choice` counts the (menu, key) groups that carried no
  flag and receive the default business choice when the datasets are formed —
  nothing is dropped for a missing flag (`menus_rows_dropped_no_choice` is
  always `0`); see [your previous business
  policy](03-data-format.md#your-previous-business-policy-what-historically_chosen-marks).
  An unexpected `"absent"` means your column flagged nothing (a
  `TRUE`/`FALSE` export, a locale that wrote `1,0`). Each counter's exact
  granularity — row, cell, or whole group — is tabulated in
  [what intake drops](03-data-format.md#what-intake-drops-and-what-it-reports).
- `model` — the model version this fit will run on.
- `business_description_source` — where the fit's
  [business description](02-endpoints.md#business-description) came from:
  `request`, `account_profile` (console Business profile), or `last_sent`
  (reused from the account's previous fit).
- `grounding_mode` — the applied
  [grounding mode](02-endpoints.md#grounding-modes): `business_led` (what an
  omitted field means) or `client_grounded`. Always a concrete mode, so this is where you confirm
  what an omitted field or a `default`/`auto` alias resolved to.
- `parse_report.client_labeled_rows` — under
  [`client_grounded`](02-endpoints.md#bringing-your-own-labels-client_grounded),
  how many of your own labels were accepted and published verbatim. `0` in
  the derived modes, which recompute instead.
- `parse_report.checks` — `on` or `off`, recording whether the
  [plausibility checks](02-endpoints.md#turning-the-plausibility-checks-off)
  ran. A fit submitted with `"checks": "off"` always says so here and in the
  published task's metadata.

## Common 422 errors

| message contains | fix |
| --- | --- |
| `menu 0 is reserved for the task` | move historical rows off menu 0. |
| `T=0 task rows must use the reserved menu id 0` | set `menu = 0` on the task rows. |
| `no menu-0 (T=0) task rows` | include the current menu you want predicted. |
| `dated after now (T > 0)` | your Sales contain future rows — trim to history. |
| `outside the replay horizon` | a sale is dated more than `inventory_holding_weeks_before_writeoff` after its menu (or before it). |
| `unit_fee differs between rows of one key` | `unit_fee` is one value per key, charged on every unit **ordered**. Send the same value on every Sales row of the key, or on one `qty = 0` placeholder row — see [per-position charges](03-data-format.md#per-position-charges-unit_fee-is-charged-on-ordered-units). |
| `unit_fee given for keys whose menus rows lack a positive unit_cost` | the fee is applied as a fraction of the key's cost basis, so the key's historical Menus rows need a positive `unit_cost`. |
| `keys appear in historical menus at multiple T values` | split those into distinct keys or separate requests. |
| `grounding failed: ...` | economics couldn't replay — the message names the failing constraint (e.g. non-integer sales qty). |
| unknown `model` version | check `GET /` for the versions this server offers. |
| `client_grounded: no historical row carries a profit` | use `business_led` for standard member/agent workflows. `client_grounded` is reserved for enterprise use after consultation with HyperC; in an agreed integration, supply the validated historical labels your pipeline produced. See [enterprise grounding](02-endpoints.md#bringing-your-own-labels-client_grounded). |
| `unknown checks value ...; expected 'on' or 'off'` | the [`checks`](02-endpoints.md#turning-the-plausibility-checks-off) switch takes only `"on"` and `"off"`. |
| `business_description could not be resolved` | none of the three sources exists: send `business_description` in the request (the business **and** its unit economics — fees, accumulated/holding costs, approximations OK), or save one in the console's Business profile — see [Business description](02-endpoints.md#business-description). |

Other statuses you may meet: **401/403** — missing/invalid API key, or a
feature your account isn't flagged for; **413** — request over your plan's
size cap. Reduce the payload (for example, provide fewer menus or historical rows) and retry; **501** — you asked for `business_led`
[grounding](02-endpoints.md#grounding-modes) on a deployment that does not
run that pipeline (`default` and `auto` also resolve to `business_led`; they do not bypass this refusal); **429** — no active subscription (subscribe in the console), or
the plan's compute budget is exhausted for the current weekly or monthly
window (see utilization in the
[management console](https://api.hyperc.com/app/)).

A real free-key request for a market outside the supported set returns HTTP
**403** with `detail.code: "free_markets_only"` and the exact message
`free tier only supports select markets, including t5market.com.` The request
is not accepted and has no `session_id`. See [Free workspace fits](02-endpoints.md#free-workspace-fits)
for the canonical eligibility contract. A separate `mock: true` input test can validate the
same input, but it does not change eligibility for an actual fit.

### `workspace_context` refusals

A `/fit` that carried a
[`workspace_context`](02-endpoints.md#binding-a-fit-to-a-workspace-project) the
service could not bind is refused with 422 before the request is spooled or
billed — nothing is charged and no `session_id` exists. The `detail` is
`workspace_context: <reason>`:

| reason | fix |
| --- | --- |
| `must be an object {project_id, run_id}` | send the field as an object. A value of the wrong JSON type is usually caught earlier still, by request validation, and comes back as the framework's standard field-validation error rather than this string. |
| `missing project_id` | the object has no non-empty `project_id`. |
| `missing run_id` | the object has no non-empty `run_id`. |
| `bad id` | an id contains characters the service does not accept (`A-Z a-z 0-9 _ . : -`, up to 80 characters). Send the ids exactly as your workspace issued them. |
| `this account has no live workspace to bind to` | this key has no workspace to resolve the ids against — submit without `workspace_context`, and the feedback stays scoped to the API session. |
| `project_id is not registered in your workspace` | your workspace does not hold a project with that id (an id from another account's workspace reads the same way). Create the project there first, or correct the id. |
| `run_id is not a run of that project` | the project exists but has no such run. Mint the run in that project before submitting. |
| `your workspace could not be reached to verify project_id (...)` | the workspace did not answer, so the binding could not be checked — an unverifiable binding is never assumed. Retry, or submit without `workspace_context`. |

## Single-quantity offers will not pass

Before submitting, count distinct quantity choices per offer `(menu, key)`.
One row per offer is not sufficient; the business formulation must support at
least three distinct meaningful quantities and profits that depend on size.
A large total row count does not repair single-point offers. More meaningful
quantity points are better; duplicating rows or inventing labels is not a fix.

Reformulate inventory units, money quanta for loans or bids, or historically
similar domain buckets as described in the
[quantity guide](03-data-format.md#multiple-quantity-choices-are-required).
Check the historical option structure and current executable menu separately.
A successful mock/format check does not prove this fit requirement is met;
turning plausibility checks off does not make a one-point business valid.

## Fit-time (cluster) failures

`POST /fit` validates shape, not statistics: a request can pass intake and
still fail when the calculation runs on the cluster. These surface as
`status: "failed"` on `GET /result/{session_id}`, with the reason in `error`:

| `error` contains | meaning | fix |
| --- | --- | --- |
| `Unlabeled business-menu mask selected zero rows` | the history contains only observed outcomes — no unlabeled context for the model to contrast against. P34 needs both halves of a [partially observed market](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement) | include the groups with no trustworthy outcome — `profit` blank on every row of the group, no flag needed — see [the data-format guide](03-data-format.md#include-the-deals-you-did-not-take) |
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
  rows only — 139 of them above, not all 2,526. Gate: `p80 ≤ 0.10` and the
  tail `≤ 0.30`, where the tail is `p98` when at least 100 rows disagree and
  `p95` below that (the message says which), so that a single row cannot veto
  a fit. `p98 = 1.0` means at least one row has the opposite sign.
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

Two shapes have one specific cause each, and the message names them when the
arithmetic matches:

- **one-signed, confined to keys that carry a `unit_fee` and sold less than
  they ordered, each gap equal to `unit_fee × (ordered − sold)`** — the fee was
  spread over the units that sold; the contract charges it on every unit
  ordered. Resend `unit_fee = charge / qty ordered`, the same value on every
  row of the key — see
  [per-position charges](03-data-format.md#per-position-charges-unit_fee-is-charged-on-ordered-units).
- **loss positions with no sales on the tape that the replay shows as gains or
  as smaller losses, everything else exact** — a per-position charge never
  reached the tape (it sits in a feature column, or only in the description).
  Put it on a `qty = 0` placeholder row of the key as `unit_fee`.

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

## Current-market freshness and limits

If result feedback says the market moved to a newer state, fetch its latest
current-menu data and resubmit `/fit`. Reordering old rows does not refresh
quotes. Use `T=0` and `menu=0` for the current options; there is no public
top-level `tick` request field. Historical `T` values remain relative periods.

A request may carry at most 100,000 menu rows, current and historical rows
together; a larger request is refused at submission with the size feedback.
The history you send is labeled and expanded by the market within a fixed row
budget: when every quantity of every settled deal does not fit, each deal
receives the same evenly spaced subset of quantities instead, so more history
is served more coarsely rather than refused. If `/result` feedback still names
the payload size, reduce menu or history rows and submit a fresh current menu.
The plan's HTTP request cap and downstream preparation limits are separate; an
initial HTTP 200 does not guarantee the latter was satisfied.

Free-market fits currently default to 4 requests per hour and 100 per day.
These are configurable limits; follow the API's returned rate-limit feedback.
Input-test mode does not grant eligibility for an actual free-market fit.
