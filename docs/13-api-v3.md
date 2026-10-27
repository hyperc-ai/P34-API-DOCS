# 13. API v3 — send your history once, then score each new menu

Base URL: **`https://api.hyperc.com/v3`**

v3 is [API v2](11-api-v2.md) with a **context cache**. The first fit sends
your history, exactly as in v2: P34 grounds it, fits its analysis and answers
in updates. It then **keeps** the grounded history and the fitted analysis as
a **context**. Each later fit names that context and sends **only the new
menu**. Only the menu is grounded; the kept analysis scores it and selects the
trades. The answer comes back as in v2: updates that only add trades, until
the portfolio is `final`.

A cached fit skips the two slow and costly parts of a fit, grounding your
history and fitting the model. It usually answers sooner and, when its
analysis steps score from the cache, costs a small fraction of a full fit.
A step the context could not keep runs in full ([cost](#cost)).

v1 and v2 are unchanged. Pick v3 when the same business sends a new menu more
often than its history changes enough to matter.

## Endpoints

| Method & path | Purpose |
| --- | --- |
| `GET /` | What this server offers: the model names (`compounds`), how long a context lives (`context.ttl_seconds`, `context.max_age_seconds`), the limits (`limits.max_ready_per_account`, `limits.tag_max_chars`, `limits.idempotency_key_max_chars`, `limits.anchor_max_json_chars`), and how a cached fit counts towards the fits a plan includes (`reuse_counts_in_fit_window`, [below](#fits-included-in-a-plan-fit_window)). |
| `POST /fit` | The v2 body plus an optional `context` object. Without `context`, the fit runs as in v2 and keeps a context. With `context.id`, it reuses that context. |
| `POST /context` | Build a context ahead of the next menu. Takes a full fit body, with or without T=0 rows. No portfolio is served. |
| `GET /context/{context_id}` | One context: its status, its age, and when it expires. |
| `GET /contexts` | Your contexts, newest first (at most 200). `?tag=` keeps those with your label. |
| `DELETE /context/{context_id}` | Drop a context now. |
| `GET /result/{session_id}` | The v2 result document, plus a `context` block and the cost of each update. |
| `DELETE /session/{session_id}` | Stop further analysis, as in v2. `?finish_context=true` stops serving the portfolio but lets the context finish building. |
| `POST /validate`, `GET /health` | As in v1, but with your key, like every v3 call. `GET /account/*` stays on [v1](06-token-wallet.md). |

Every v3 call, `GET /` and `GET /health` included, needs an account API key
(`Authorization: Bearer <key>`, as in [v1](02-endpoints.md#authentication)).
A missing, unknown or revoked key, or a `free-` workspace key, is answered
`404 {"detail": "Not Found"}` (where v1 answers 401 or 403), mock fits
included: free keys run mock fits on v2, not on v3. Keys, tokens and the
wallet are the same as in v1 and v2. v3 has no interactive reference page.

## Creating a context

Send the v2 body ([endpoints](02-endpoints.md),
[data format](03-data-format.md)) to `POST /v3/fit`. The fit runs exactly as a
v2 fit, answers in updates, and keeps what it grounds and fits. An optional
`context` object labels it:

```json
{ "menus": [...], "sales": [...], "market_type": {...},
  "business_description": "...",
  "context": {"tag": "eu-shop", "idempotency_key": "eu-shop-2026-10-27T09"} }
```

| `context` field | meaning |
| --- | --- |
| `create` | `true` (the default) keeps a context. `false` runs a plain v2 fit at the v3 address. |
| `tag` | Your label for the context, for example the business it belongs to; up to 128 characters. A newer context with the same tag **replaces** the older ones once it is `ready` and serves at least as many analysis steps as each of them (`servable_models`), or once all of its steps have finished ([lifetime](#lifetime)). |
| `idempotency_key` | Up to 64 characters, unique per account. Sending the same key again builds nothing and answers with that create's session and context as they are now: `session_id`, `status`, `more_expected`, `poll`, `context_id`, the `context` block and `idempotent_replay: true` (on `POST /v3/context`: `context_id`, `status`, `build_session_id`, `poll`, `result`, `idempotency_key`, the `context` block and `idempotent_replay: true`). It does not repeat the first answer's `parse_report` or `billing`. Retry a timed-out create with the same key. Mock creates are not deduplicated. |
| `anchor` | Any JSON value of up to 256 characters, kept with the context and returned as `history.anchor` (present only when the create sent an `anchor`): for example your own marker of the last menu the history includes. |

Any other field in `context` (besides `id` and `on_mismatch`, which a
[reuse](#reusing-a-context) sends) is refused with 422.

The acknowledgement is v2's (`session_id`, `status`, `more_expected`, `poll`,
`parse_report`, `billing`, …) plus the new context's id and its `context`
block (the block `GET /v3/context/{context_id}` returns, described
[below](#context-status)), marked `created: true` and `role: "build"`:

```json
{ "api_version": "v3", "session_id": "751f…", "status": "grounding",
  "more_expected": true, "poll": "/v3/result/751f…",
  "context_id": "ctx_9c11df6d8c754983ba4eb869",
  "context": {"id": "ctx_9c11df6d8c754983ba4eb869", "status": "building",
              "tag": "eu-shop", "created_at": "2026-10-27T09:00:20+00:00",
              "expires_at": "2026-11-03T09:00:20+00:00", "uses": 0,
              "created": true, "role": "build", "…": "…"} }
```

Keep `context_id`: every later fit names it.

A context is kept for [business-led](02-endpoints.md#grounding-modes) fits
on the default grounding (no non-default `grounding_executor`). A fit that
cannot keep one still runs, as a plain v2 fit, and its acknowledgement says so:
`"context": {"created": false, "reason": "executor"}`. A partner-market fit
is refused on v3 (`422 context_not_supported`, reason `partner`): as in v2,
partner-market fits run on `/v1/fit` only.

**When a context is ready.** A context becomes `ready` once its grounded
history and at least one fitted analysis step are kept. That is usually while
the deeper analysis of the first fit is still running; steps that finish later
join the context as they finish; until then a reuse waits for them
([below](#waiting-for-steps)). Not every step succeeds on every history. A
context holds the steps that did, and a cached fit scores those from the
cache. A step the context could not keep may run in full on each reuse
(`context.models`, [below](#context-status)).

P34 also checks that the kept history can ground a new menu
(`grounding.menu_reusable`, [below](#context-status)). A context that fails
this check is `failed`, even if it was already `ready`, and a reuse of it is
handled as `on_mismatch` says ([below](#reusing-a-context)).

## Reusing a context

Name the context and send only the new menu:

```json
{ "menus": [{"key": "B101", "menu": 0, "T": 0, "qty": 2.0,
             "unit_cost": 10.0, "unit_price": 14.0, "...": "your other menu columns"}],
  "context": {"id": "ctx_9c11df6d8c754983ba4eb869"} }
```

The rules for that body (a refusal comes before anything runs):

- `menus` holds **only T=0 task rows** (`menu = 0`, `T = 0`, no `profit`),
  checked as in v1. A history row is refused with
  `422 context_history_not_allowed`.
- The columns are **the columns of the menus the context was built from**
  (`history.raw_schema` in the context lists them, with their types):
  no new column and none missing, in any order. The outcome columns
  (`profit`, `historically_chosen`, `historically_available`) may be left out.
  Each value must convert to the type its column had then: a text key where
  the first fit sent numbers, for example, does not. Otherwise
  `409 context_stale` (reason `schema`; `detail.extra_columns`,
  `detail.missing_columns` or `detail.columns` name them).
- If the context's keys were numbers, every key of the new menu must be a
  number too; otherwise `409 context_stale` (reason `keys`). Other keys may
  be new: they are coded on top of the context's.
- `sales` is not needed, and is ignored if sent.
- `business_description` may be left out. If you send it, it must be the
  context's text; only runs of whitespace count as one space.
  Otherwise `409 context_stale` (reason `description`).
- `model` must be the context's model (`context.model`): send that name, or
  leave `model` out when it is `default`. Another model is refused with
  `422 context_model_mismatch` (`detail.context_model` names the context's).
- `market_type` may be left out, but a model named inside it
  (`market_type.model`) is not kept: then send that model as `model`. If you
  send `market_type` and it holds a `business_description`, the rule for
  `business_description` above applies to it.
- `confidence_correction`: leave it out to apply the first fit's. A different
  value is honoured: the analysis steps that apply a correction then run in
  full for this fit and are billed as full steps, while the context keeps its
  own; the others score from the cache.

`context.on_mismatch` decides what happens when the new menu cannot be
grounded against the kept history after all: for example because grounding
this menu would treat the history differently from the first fit, because
the context's kept history cannot ground new menus
(`grounding.menu_reusable: false`), or because P34 cannot ground menus for
this context right now.

| value | what happens |
| --- | --- |
| `"rebuild"` (default) | The fit runs **in full** on the context's kept history plus your new menu, and keeps a **new** context that replaces the old one. Its result says so in `context.fallback`, `context.id` names the new context, and it is billed as a full fit; the wallet and your plan's [fit window](#fits-included-in-a-plan-fit_window) must allow a full fit ([cost](#cost)). When P34 can tell at once, the acknowledgement already is that of the new build (a new `session_id` and `context_id`). |
| `"fail"` | Nothing is rebuilt. When P34 can tell at once, the fit is refused with `409 context_mismatch`. When only the grounding of the menu finds it, the session ends `failed` with `error_code: "context_mismatch"`, and `context.error` holds the 409 in the same shape: `{status: 409, code, reason, message}`. Nothing is charged for the analysis. |

The acknowledgement of a reuse is v2's grounding acknowledgement
(`status: "grounding"` while the menu is grounded) with `context_id` and the
`context` block, marked `role: "reuse"`. Poll it as any v2 session.

### Waiting for steps

A reuse waits for every analysis step whose kept model is still on its way
(`pending` or `building` in `context.models`). Updates are served in step
order, so the updates after a waiting step wait too. When the model is
built, the step goes on as any other (usually scored from the cache). A step
whose model is still not built after about one and a half times a typical
build is skipped (`stage_fallbacks` reason `context_wait_timeout`,
[below](#results)), and the next step goes on.

This happens on a `ready` context too: a context is usually `ready` while the
first fit's deeper analysis is still running. A reuse sent then waits for
those deeper steps, and its `context` carries no `wait`. Read the states in
`context.models`, not `wait`, to predict the delay.

A reuse may also name a context that is **still building**, once the
grounding of its history is kept (`grounding.retained: true`): the
acknowledgement's `context` then says `wait: true`. Before that point the
answer is `409 context_not_ready` with `retry_after` (seconds, also in the
`Retry-After` header).

### What a reuse means

A cached fit scores your new menu **against the context's history and sales
as they were when the context was built**. P34 dates the new menu at the
first fit's task date (`history.task_date`), as if it had been offered then.
`context.age_seconds` in every result tells you how long ago the context was
created. Sales, outcomes and labels that arrived after the build are not seen
by a cached fit.

Refresh, by creating a new context from your latest history, when that
matters: after new outcomes have settled for a meaningful share of your
deals, after a large backfill, or when the market has moved. Between
refreshes, keep the business description and the menu columns unchanged.
Either change makes the context unusable (`context_stale`).

## Building ahead: `POST /v3/context`

A create runs at the pace of a full fit. If your menus arrive faster than
that, build the next context before the menu exists:

```
POST /v3/context      the full fit body: history, sales, description, …
→ {"api_version": "v3", "context_id": "ctx_…", "status": "building",
   "build_session_id": "…", "context": {…}, "poll": "/v3/context/ctx_…",
   "result": "/v3/result/…", "idempotency_key": "…"}
```

- T=0 rows are optional. Without them, P34 makes a stand-in menu from your
  latest history menu (fresh keys, no outcomes; `history.placeholder: true`)
  and uses it only to check the build from end to end.
- It runs everything a create runs, and is billed like one. No portfolio is
  served, on any result route: `GET /v3/result/{build_session_id}` shows the
  status and the `context` block, with `menu: []`, `n_selected: 0` and
  `context_only: true`.
- `tag`, `idempotency_key` and `anchor` work as in a create, inside `context`
  in the body; the answer echoes `idempotency_key`. A body that cannot keep a
  context is refused with `422 context_not_supported` (reason `executor`, or
  `partner` for a partner-market fit) before anything runs.
- Follow `GET /v3/context/{context_id}` until `status` is `ready`, then send
  the menu as a reuse. If it reads `failed`, `expired` or `dropped` instead,
  build again, or send the full body as a create when the menu is due.

## Context status

`GET /v3/context/{context_id}` answers `{"api_version": "v3", "context": {…}}`;
`GET /v3/contexts` answers `{"api_version": "v3", "contexts": [{…}, …]}`.

| status | meaning |
| --- | --- |
| `building` | Being built. A reuse can wait for it once its history grounding is kept (`grounding.retained`). |
| `ready` | Reusable. |
| `failed` | The build kept no usable context: its grounding failed, its kept history cannot ground new menus, or no analysis step could be kept. Create a new one. |
| `expired` | Past its lifetime ([below](#lifetime)): unused too long, or past its maximum age. |
| `dropped` | Deleted by you, replaced by a newer context (one with the same `tag`, or the new context of a `fallback`), or dropped to stay within the number of ready contexts an account keeps. |

| field | meaning |
| --- | --- |
| `id`, `tag`, `idempotency_key` | As created. |
| `build_session_id` | The session that built it. |
| `model` | The model it was built with; a reuse runs the same one. |
| `created_at`, `ready_at`, `last_used_at`, `expires_at` | ISO times. While building, `expires_at` is the maximum age; every use moves it on, never past the maximum age. |
| `age_seconds` | Seconds since the context was created. |
| `uses` | How many cached fits used it. |
| `models` | One entry per analysis step (keyed by the step's internal name): `state` (`pending`, `building`, `ready`, `failed`, `skipped`, `stale`), `instant` (`null`, or `{kind, detail}` when the step's verdict holds for every menu, [below](#results)) and `error`. A reuse waits for a `pending` or `building` step ([waiting](#waiting-for-steps)). A `stale` or `skipped` step, and a `failed` one whose failure was not about your data, may run in full on every reuse (`role: "heal"`, billed as a full step); other failed steps are skipped. |
| `servable_models` | The steps a cached fit scores from the cache: those `ready` without an `instant` verdict. They are what the cache saves. |
| `history` | What the context's history holds: `menus`, `rows`, `labeled_rows`, `keys`, `key_mode` (`string` or `numeric`), `task_date`, `placeholder`, your `anchor` (present only when the create sent one), and `raw_schema`: the columns of the menus it was built from, in order, with their types (`[[column, type], …]`, for example `["key", "string"]`, `["qty", "int64"]`, `["unit_price", "double"]`), which a reuse sends. |
| `grounding` | `menu_reusable` (`null` until P34 has checked that the kept history can ground a new menu, then `true` or `false`), `menu_seconds` (how long grounding a menu took), and `retained` (`true` once the grounded history is kept and not found unable to ground a menu: from then on a reuse of a `building` context waits instead of answering `context_not_ready`). |
| `dropped_at`, `drop_reason`, `superseded_by` | When and why it ended (`member`: you dropped it; `superseded`: replaced by `superseded_by`; `capacity`: over the account's limit; `expired`), and the context that replaced it. |

## Results

`GET /v3/result/{session_id}` returns the
[v2 document](11-api-v2.md#statuses-polling-does-not-stop-at-the-first-portfolio):
the same statuses (`partial` while `more_expected`, then `final`), the same
union rule (a served trade is never withdrawn or resized) and the same
`added_in_update`. Two things are added:

- a `context` block: the context's block ([above](#context-status)) plus
  this session's `role` and what happened to it (below);
- `billing.updates`: per update, the tokens its analysis step was charged
  (`runtime_tokens`, `null` until it settles), the `role` it ran under, and
  `instant: true` for an update answered from a kept verdict. It appears
  with the first update.

```json
{
  "api_version": "v3", "status": "final", "more_expected": false,
  "session_id": "898f…", "model": "default", "update": 3,
  "menu": [
    {"key": "B101", "menu": 0, "T": 0, "qty": 1.0, "profit": 4.0, "added_in_update": 1},
    {"key": "B102", "menu": 0, "T": 0, "qty": 2.0, "profit": 8.0, "added_in_update": 3},
    {"key": "B103", "menu": 0, "T": 0, "qty": 0.0, "profit": 0.0, "added_in_update": null}
  ],
  "n_selected": 2, "predicted_profit_sum": 12.0,
  "updates": [{"update": 1, "new_trades": 1, "…": "…"},
              {"update": 2, "new_trades": 0, "…": "…"},
              {"update": 3, "new_trades": 1, "…": "…"}],
  "final_reason": "complete",
  "context": {"id": "ctx_9c11df6d8c754983ba4eb869", "status": "ready",
              "age_seconds": 86400, "expires_at": "2026-10-31T09:00:24+00:00",
              "uses": 1, "…": "…", "role": "reuse"},
  "billing": {"updates": [
    {"update": 1, "runtime_tokens": 0.0371, "role": "reuse"},
    {"update": 2, "runtime_tokens": 0.0, "role": "reuse", "instant": true},
    {"update": 3, "runtime_tokens": null, "role": "heal"}]}
}
```

(The token figures only show the shape; each charge's arithmetic is in your
ledger.)

| `context` field | meaning |
| --- | --- |
| `id` | The context this fit built or used. After a `fallback`, the new context. |
| `role` | `build` (this fit creates the context) or `reuse`. |
| `wait` | `true` only when the context itself was still `building` when this reuse was accepted. A reuse of a `ready` context also waits for steps still on their way, without `wait` ([waiting](#waiting-for-steps)). |
| `fallback` | Present only when this fit could not use the context and was turned into a **full fit that keeps a new context**: `{reason, detail, replaces}`. `reason` is a short code for why, `detail` a fixed sentence that explains that code (for example `{"reason": "grounding", "detail": "the context's kept grounding cannot ground a new menu", "replaces": "ctx_…"}`), and `replaces` the old context, now `dropped` with `superseded_by` set. Use the new `id` from now on. |
| `stage_fallbacks` | Present only when, during this fit, a step's score from the cache failed, or a step was skipped because the model it waited for was not built in time: `[{stage, reason, action, at}]`. `stage` is the step's position in the model (1 = the first, quickest step), not its name in `context.models` and not an update number; `reason` is a short code (`context_wait_timeout` for a wait that ran out); `at` an ISO time. `action` `heal`: that step was fitted again for this menu on the context's kept history, and billed as a full step; `skip`: it added no update. Steps planned to run in full from the start are not listed: they show as `role: "heal"` in `billing.updates`; a step skipped from the start just adds no update. The context id is unchanged: keep using it. |
| `error` | Only on a reuse sent with `on_mismatch: "fail"` whose menu could not be grounded against the context: `{status: 409, code: "context_mismatch", reason, message}`. |

In `billing.updates`, `role` is `build`, `reuse` (scored from the cache), or
`heal` (a step that ran in full inside a cached fit). `instant: true` marks an
update answered at once from a kept verdict: a step that, on this history,
declined to trade at all answers every cached fit with no trades and costs
nothing.

A whole fit becomes a full one (`fallback`) only before anything of it was
scored. Once its steps are out, a step whose kept model cannot be used runs
in full for that step only, or is skipped (listed in `stage_fallbacks` when
this is found during the fit), and the portfolio served so far always
stands. If no step at all could answer, the
session ends `failed` with `error_code` `context_model_unavailable` (send the
fit with its history to build a new context) or `context_expired` (the
context ended long before the menu could be scored: a reuse accepted before
its context was dropped or expired normally still finishes on it,
[below](#lifetime)).

Poll v3 sessions at `/v3/result`: only it carries the `context` block and the
per-update billing.

## Stopping

`DELETE /v3/session/{session_id}` works as in v2. The steps that are running
are canceled, and the portfolio served so far becomes `final` with
`final_reason: "stopped"`.

On a fit that builds a context, a plain stop also stops the build, and the
context keeps only the steps that had finished. To stop serving but keep
building, add `?finish_context=true`: the result goes `final` (`stopped`) at
once (before the first update it reads `failed` with
`error_code: "fit_canceled"`, as a v2 stop does), no step is canceled, and the
remaining steps still run, are billed, and join the context. The answer says
`"finish_context": true`. On a reuse, `finish_context` changes nothing: it is
the plain stop.

## Errors

Every v3 refusal about a context carries a `detail.code`:

| HTTP | `detail.code` | when | what to do |
| --- | --- | --- | --- |
| 404 | `context_not_found` | No such context on your account. | Send the full body as a create. |
| 409 | `context_expired` | `reason`: `ttl` (unused too long), `age` (past its maximum age, or so close to it that this reuse could not finish before it), `dropped` (deleted, or dropped over the account's limit), `superseded` (replaced by a newer context with the same tag, or by the new context of a `fallback`; `superseded_by` names it), `grounding` (a rebuild was due, but the context's kept history is gone). | Send the full body as a create. |
| 409 | `context_stale` | `reason`: `schema`, `description` or `keys` (see the rules above). | Send the full body as a create; it keeps a context for the new columns or description. |
| 409 | `context_not_ready` | The context's history is still being grounded: carries `retry_after`. Or, with `reason: "failed"` and no `retry_after`, its build kept nothing usable. | Wait `retry_after`, then send the same reuse again; on `failed`, send the full body as a create. |
| 409 | `context_mismatch` | Only with `on_mismatch: "fail"`: the menu cannot be grounded against the kept history. `reason` says why. | Send the full body as a create, or the same reuse without `on_mismatch: "fail"`. |
| 422 | `context_history_not_allowed` | The reuse body holds history rows (`history_rows` counts them). | Send only the T=0 rows. |
| 422 | `context_model_mismatch` | The reuse names another model than the context's (`context_model` names the context's). | Send `context_model` as `model` (or leave `model` out when it is `default`), or send the full body as a create. |
| 422 | `context_not_supported` | `reason` `executor`: a `POST /v3/context` body that cannot keep a context. `reason` `partner`: a partner-market fit, whether a create, a `POST /v3/context` or a reuse (as in v2, partner-market fits run on `/v1/fit` only; `message` says so). | Send a business-led body without a non-default `grounding_executor`; send partner-market fits to `/v1/fit` with their history. |

A malformed `context` object is refused with 422 and a plain-text `detail`
that starts with `context:`. Nothing runs and nothing is charged for a refused
call. Everything else (authentication, wallet and plan refusals, validation
of the menu rows, fit failures) is as in [v1](04-errors-and-checks.md) and v2.

## Lifetime

- A context **unused for 3 days** expires.
- A context expires **7 days after it became ready**, however often it is
  used. This bounds how old a cached view of your history can get. A context
  that never becomes ready ends 7 days after it was created, and a `failed`
  one is kept 3 days so you can read it.
- Every reuse moves `expires_at` on, up to that maximum.
- `GET /v3/` gives both limits as `context.ttl_seconds` and
  `context.max_age_seconds`; when they differ from this page, the numbers it
  returns are the ones that apply.
- An account keeps a limited number of ready contexts
  (`limits.max_ready_per_account` in `GET /v3/`). When one more becomes
  ready, your least recently used ready contexts are dropped
  (`drop_reason: "capacity"`).
- When a context with a `tag` is ready, your older contexts with the same
  `tag` are dropped (`drop_reason: "superseded"`) as soon as it serves at
  least as many analysis steps as each of them (`servable_models`), or once
  all of its steps have finished. Until then an older context keeps serving,
  so a deeper step it holds is not lost to the newer one's first, quickest
  step.
- A dropped or expired context accepts no new reuse from that moment, but the
  reuses it had already accepted still finish on it. Only a reuse that is
  still not scored hours after its context ended fails, with `error_code`
  `context_expired`.
- Because nothing moves the maximum age, a reuse is refused with
  `409 context_expired` (reason `age`) once the context would reach its
  maximum age before the reuse could finish.
- `DELETE /v3/context/{context_id}` drops a context now
  (`drop_reason: "member"`) and answers `{"ok": true, "api_version": "v3",
  "context": {…}}`. Dropping it again is harmless.

## Cost

- A **create**, and a **`POST /v3/context`**, cost what a v2 fit costs: the
  grounding of your history plus the compute of every analysis step.
- A **cached fit** is billed only for **scoring**: the compute the kept
  analysis spends predicting your new menu, with a small minimum per step.
  There is no history grounding, no model fit, and no separate charge for
  grounding the new menu, so when its steps score from the cache it costs a
  small fraction of a full fit. Its [ledger](06-token-wallet.md) entries say
  `cached context` and name the context.
- A step answered from a kept verdict (`instant`) costs nothing.
- A step that runs in full inside a cached fit (`role: "heal"`: a different
  `confidence_correction`, a step the context could not keep for this
  history, or a kept model that could not be used) is billed as a full step.
  A step the context could not keep runs in full on every reuse
  (`context.models`, [above](#context-status)), so a cached fit can cost
  close to a full fit minus the history grounding. A fallback to a full fit
  (`context.fallback`) is billed as a full fit.
- A fallback is admitted like a create: the wallet check and your plan's
  [fit window](#fits-included-in-a-plan-fit_window) apply at full-fit price,
  before your history is grounded again. When P34 can tell at once, a
  refusal is the `429` a create would get. When
  only the grounding of the menu finds the mismatch, the session ends
  `failed` with `final_reason` `budget_exhausted` or `fit_window`, and
  nothing is charged.
- The wallet check before a cached fit uses the scoring estimate of its
  first step (the full estimate when that step runs in full, for example for
  a different `confidence_correction`); each further step is checked as it
  is sent. A step the wallet cannot pay for, and the steps after it, do not
  run: the session ends `final` with `final_reason: "budget_exhausted"`, as
  in v2.

The rates are not restated here, because they change. Each charge's
arithmetic is in its ledger entry's `msg`.

### Fits included in a plan (`fit_window`)

Some plans include a number of fits of each kind (quick, statistical and
full) per window, on top of paying for them from the wallet. Plans without
such a limit pay for every fit from the wallet, and nothing here applies to
them. `GET /v3/` describes the rule in `fit_window`; the figures are on the
plans page and are not restated here, because they change.

- A fit beyond what is left of its kind is refused with `429` and
  `detail.code: "fit_window"` (with `detail.resets_at`, when the window
  refills). Nothing runs and nothing is charged; wait until then. It is
  neither a data problem nor the wallet.
- A later step beyond it does not run: the session ends with
  `final_reason: "fit_window"`, and the portfolio served so far stands.
- `reuse_counts_in_fit_window` in `GET /v3/` says how a step scored from the
  cache counts: `limited_tiers_as_naive`, as a quick fit; `as_model`, as its
  model's own kind; `never`, not at all. A step that runs in full always
  counts as its own kind.

## Mock mode and limits

- `"mock": true` works as in v2: creates and reuses are simulated on the
  `mock_result_seconds` timer. Nothing is grounded, kept or charged.
- A mock create returns a `context_id` for a simulated context: `building`
  until the timer runs out, then `ready` (`failed` with `"mock": "failed"`).
  A mock reuse (`"mock": true` in the reuse body) accepts only such a
  simulated context, and a real reuse only a real one; the other answers
  `404 context_not_found`. So a client in mock mode sends `"mock": true` in
  its reuses too, not only in its creates. `GET` and
  `DELETE /v3/context/{context_id}` work on simulated contexts;
  `GET /v3/contexts` does not list them.
- The limits of v2 apply to v3 as well.

## A client loop

With curl, a create, then a reuse:

```bash
# 1. The first fit: the full v2 body plus a context label; P34 keeps a context.
curl -s https://api.hyperc.com/v3/fit \
  -H "Authorization: Bearer $P34_API_KEY" -H "Content-Type: application/json" \
  -d @full_request.json
# -> {"session_id": "…", "context_id": "ctx_…",
#     "context": {"id": "ctx_…", "created": true, "role": "build", …}, …}

# 2. The next menu: only its T=0 rows, naming the context.
curl -s https://api.hyperc.com/v3/fit \
  -H "Authorization: Bearer $P34_API_KEY" -H "Content-Type: application/json" \
  -d @menu_only_request.json      # {"menus": [...], "context": {"id": "ctx_…"}}
                                  # plus "model" and "mock" if the create sent them

# 3. Poll either session exactly as in v2.
curl -s https://api.hyperc.com/v3/result/<session_id> \
  -H "Authorization: Bearer $P34_API_KEY"
```

In Python, a loop that reuses while it can and creates when it must:

```python
import os, time, requests

BASE = "https://api.hyperc.com/v3"
HEADERS = {"Authorization": f"Bearer {os.environ['P34_API_KEY']}"}
# refusals after which nothing ran and a create is the answer
CREATE_INSTEAD = {"context_not_found", "context_expired", "context_stale",
                  "context_not_ready", "context_mismatch", "context_model_mismatch"}
# a reuse that ended failed with one of these scored nothing: create instead
CREATE_AFTER = {"context_model_unavailable", "context_expired"}
# what a reuse repeats from the create: its model, and mock or real
REUSE_KEEPS = ("model", "market_type", "mock", "mock_result_seconds")

def follow(session_id):
    """Poll one session as in v2; act on each update's new trades."""
    seen = 0
    while True:
        r = requests.get(f"{BASE}/result/{session_id}", headers=HEADERS)
        r.raise_for_status()
        res = r.json()
        if res["status"] in ("partial", "final") and res["update"] > seen:
            new = [row for row in res["menu"]
                   if row["added_in_update"] and row["added_in_update"] > seen]
            place_orders(new)                  # act on the new trades now
            seen = res["update"]
        if res["status"] in ("final", "failed"):
            return res
        time.sleep(15)

def fit(full_body, menu_rows, context_id):
    """Reuse context_id for this menu; fall back to a create that keeps a new one.

    full_body is the v2 body with your latest history and this menu's T=0 rows;
    menu_rows are those T=0 rows alone. Returns (result, context id to use next).
    """
    if context_id:
        reuse = {"menus": menu_rows, "context": {"id": context_id},
                 **{k: full_body[k] for k in REUSE_KEEPS if k in full_body}}
        while True:
            r = requests.post(f"{BASE}/fit", headers=HEADERS, json=reuse)
            try:
                detail = None if r.ok else r.json().get("detail")
            except ValueError:                 # not JSON, e.g. a proxy's error page
                detail = None
            code = detail.get("code") if isinstance(detail, dict) else None
            if code == "context_not_ready" and "retry_after" in detail:
                time.sleep(detail["retry_after"])  # its history is still grounding
                continue
            break
        if r.ok:
            res = follow(r.json()["session_id"])
            if not (res["status"] == "failed"
                    and res.get("error_code") in CREATE_AFTER):
                # After a fallback the block names the new context: use it from now on.
                return res, (res.get("context") or {}).get("id", context_id)
            # no step could score this menu on the context: build a new one below
        elif code not in CREATE_INSTEAD:
            r.raise_for_status()               # wallet, plan or input refusal, as in v2
        # otherwise nothing ran, nothing was charged: send the full body instead
    r = requests.post(f"{BASE}/fit", headers=HEADERS,
                      json={**full_body, "context": {"tag": "eu-shop"}})
    r.raise_for_status()
    ack = r.json()
    res = follow(ack["session_id"])
    return res, ack.get("context_id")      # None when this fit could not keep one
```
