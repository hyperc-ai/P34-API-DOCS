---
name: p34-submit-and-monitor
description: Use when a prepared P34 request has to reach `/fit` and be followed to a result — validating it against the documented rules first, taking authorization from the caller's own key source, testing the inputs, tracking the accepted `session_id` through the documented statuses, and reading the diagnostics and feedback that come back. Load before the first call, and whenever the environment cannot actually make the call and the request has to be written down instead.
---

# Submit a P34 fit and follow it to a result

## What this covers

The last mile: a request body that already exists becomes a session you can
report on. Base URL, authentication, the endpoint table, the result statuses,
mock mode, model versions, wire formats and request limits are all in
[docs/02-endpoints.md](../../docs/02-endpoints.md); the fit response's fields,
the common 422s and the fit-time failure table are in
[docs/04-errors-and-checks.md](../../docs/04-errors-and-checks.md). **Read them
and link to them. Never restate those tables** — they are the source of truth
and they change.

The body itself comes from
[p34-prepare-inputs](../p34-prepare-inputs/SKILL.md) and
[p34-business-economics](../p34-business-economics/SKILL.md); what comes back
is read with [p34-interpret-results](../p34-interpret-results/SKILL.md).

**The rule everything else follows from:** the record has to match what
actually happened. Every line you write is either something a response said,
or something you did not do — and the second kind is written down as plainly
as the first.

## Grounding choice

Use `business_led` for standard member and agent work. Do not recommend,
implement or submit client-side grounding before consultation with HyperC and
agreement on an enterprise integration. Correct client grounding requires
vast compute resources and is reserved for enterprise clients preserving
private knowledge and know-how. Recorded profit calculations are still normal
input preparation; having those numbers does not justify switching modes.
If consultation has not happened, request it before proceeding with client
grounding, and continue any independent business-led input preparation.
See [enterprise client grounding](../../docs/02-endpoints.md#bringing-your-own-labels-client_grounded)
for the technical contract once that integration has been agreed.

## Workflow

### Establish a real quantity decision

Single-point offers will not pass a fit. Require at least three distinct,
meaningful quantities per offer `(menu, key)`, with size-dependent total
profit; more real sizes are better. Check both historical option structure
and current executable choices. Use inventory counts, a fixed money quantum
for loans/bids, or buckets of domains with similar historical behaviour.
Read [the formulation guide](../../docs/03-data-format.md#multiple-quantity-choices-are-required)
for the mapping and evidence rules. Document the unit, range and economics in
`business_description`. Do not duplicate offers, split quantities across keys,
or fabricate history/labels to pass. When the business cannot support the
range, report the gap and reformulate the business before submitting.

### 1. Check the request before spending anything on it

Run the cheap client-side checks first; each of them is a 422 you would
otherwise pay a round trip for
([common 422 errors](../../docs/04-errors-and-checks.md#common-422-errors)):
menu `0` reserved for the T=0 task rows, task rows present, no `profit` on a
T=0 row, at most one `historically_chosen = 1` per `(menu, key)`, Sales dated
`T <= 0` and inside the replay horizon, one `T` per key across historical
menus, a `market_type` and a resolvable
[business description](../../docs/02-endpoints.md#business-description).
Under [`client_grounded`](../../docs/02-endpoints.md#bringing-your-own-labels-client_grounded)
nothing is replayed, so the Sales, replay-horizon and description checks do not
apply; what must hold instead is that at least one historical row carries a
`profit`.

For business-led fits, also review the description for a fixed cutoff,
reproducible full or partial write-off calculation, and a dictionary of every
submitted column, as described in
[what to write](../../docs/02-endpoints.md#what-to-write-in-it). This is an
economics-quality check, not an additional 422 rule.

Two more conditions are accepted by `/fit` and fail later, so they are worth a
few lines of pandas now rather than a queue wait: enough observed groups
sharing a `qty` option, and declined groups actually present. Both are
described with their fixes in
[docs/04-errors-and-checks.md](../../docs/04-errors-and-checks.md).

These checks are yours to run, not something to ship: the request body carries
contract tables and features, never a validator.

### 2. Authorization comes from the caller's own key source

Read the key from wherever this environment already keeps it — an environment
variable, a secret file, the platform's secret store — and send it as the
documented `Authorization: Bearer` header
([Authentication](../../docs/02-endpoints.md#authentication)).

The key never appears in anything you write. Not in a log, a report, a ticket,
a request dump, a commit, or a command you paste back for someone else to run:
reference the variable (`$P34_API_KEY`) or show the header redacted. If you
are handed a file with a key already pasted into it, do not copy it forward —
use the environment and say the key should be rotated.

### 3. Serialize the way the contract documents

Tables cross as JSON records or base64 Parquet
([wire formats](../../docs/02-endpoints.md#wire-formats); both helpers are in
[`examples/client/wire.py`](../../examples/client/wire.py)). Blanks stay
`null`. A blank coerced to `0` on the way out is a fabricated observation, and
no error will tell you.

### 4. Test the inputs before a separate actual fit

Send the same body with `"mock": true`
([Input-test mode](../../docs/02-endpoints.md#mock-mode-input-testing)).
This works on every tier, including a free key testing a market outside the
free-tier supported set. It
tests input parsing and validation without grounding, compute, or billing.

**A mock result is not a prediction.** The `done` payload has the full real
shape, and its numbers are deterministic placeholders derived from your own
T=0 menu. Every mock response says so — `"mock": true` plus a `mock_note` —
and the `billing` block reports `"tokens_charged": 0`. A placeholder that
reaches a report, an order, or a profit figure is a fabricated result no
matter how it got there, so check for those markers before you read any number
out of a response, and label the run as validation wherever you write it down.

A clean input test does not prove that grounding or an actual fit will succeed,
and it does not change free-tier eligibility. Treat the later actual fit as a
new attempt with its own record and authorization decision.

### 5. Submit the real fit and keep the session id it returns

`POST /fit` answers immediately with the `session_id` everything afterwards is
keyed on. Record it verbatim the moment you have it, together with the status
the response carried. A session id you were not given does not exist, and
nothing may be attributed to one.

If you work inside a HyperC workspace, create the run first and send its ids as
`workspace_context`
([binding a fit to a workspace project](../../docs/02-endpoints.md#binding-a-fit-to-a-workspace-project));
the service then writes its process feedback next to your files, in the
project's own channel files and that run's report, instead of leaving it scoped
to the API session. The ids have to be ones your own workspace issued: an
unbindable pair is a 422 before the fit is accepted, so it costs nothing — but
it also means there is no session, and nothing to record but the refusal.

For a free key, follow the canonical
[eligibility contract](../../docs/02-endpoints.md#free-workspace-fits)
rather than maintaining your own market list. An actual request outside the
supported set is refused with HTTP 403, `free_markets_only`, and `free tier only supports select markets, including t5market.com.` It has no session to poll.
A supported-market request follows the normal fit/result workflow. Report only
the result fields and provenance the response supplies; do not invent missing
prediction, training, calibration, or model provenance.

Read the acceptance response before you start polling. For ordinary P34 fits,
some of this appears only there
([fit response fields](../../docs/04-errors-and-checks.md#fit-response-fields)):
`parse_report`, `labeled_rows` / `unlabeled_rows` / `task_menu_rows`, `model`,
`business_description_source` and `grounding_mode`. A fit that resolved a
description you did not intend, ran on a mode you did not ask for, or received
far fewer task rows than you sent is worth stopping now:
`DELETE /session/{id}` cancels a running fit.

### 6. Poll `/result` through the documented statuses

`grounding` -> `queued` -> `processing` -> `done` | `failed`
([Result statuses](../../docs/02-endpoints.md#result-statuses)). Poll on a sane
interval — tens of seconds, not a tight loop — and record each status you
observe. Large fits legitimately run for tens of minutes; `processing` for a
long time is not a failure, and the session keeps computing whether or not you
are watching.

`feedback_delivery` in each poll says where the service put this session's
process feedback and how much of it is still owed
([where feedback is delivered](../../docs/02-endpoints.md#where-feedback-is-delivered)).
Each poll retries a few of the owed entries, so a `pending` that falls to `0`
means everything landed; a `pending` that does not fall is not lost, and
`last_error` is where you read why it has not moved — no workspace to deliver
to, or one that refused the write or could not be reached. Report that reason
rather than treating the entries as missing. While the session is `grounding`
or `failed`, `feedback_log` carries the channel entries in the poll itself
(capped and truncated); the final report goes to the workspace only, so a
delivery still owed there is the one thing the poll cannot hand you.

`POST /predict` is an instant sanity check on your payload from a small
reference model. It is **not** P34's answer; `/result` is.

### 7. Report what came back, in the words the service used

- **`done`** — hand it to
  [p34-interpret-results](../p34-interpret-results/SKILL.md).
- **`failed`** — report it as failed, with its `error` string. The fit-time
  failure table in
  [docs/04-errors-and-checks.md](../../docs/04-errors-and-checks.md) names
  what each message means and how to fix it, and a fit that fails there is
  charged nothing. A failure that partly succeeded is still a failure:
  "most rows reconciled" is a diagnosis, not a pass, and the statistics in the
  message are the diagnosis worth quoting.
- **`parse_report` and the row counts** — the drop counters and an
  `historically_chosen` reading of `absent` change what the fit was given.
  Surface them.
- **free-form `feedback`** — surface it and act on it; it is written to
  improve the next request
  ([Free-form feedback](../../docs/02-endpoints.md#free-form-feedback)).

None of this is minutiae to be trimmed for length. A shorter write-up drops
detail, never the failure, the counters or the feedback.

### 8. When there is no way to execute the call

A client with no supported external HTTP transport, or no usable key in the
environment that can make the call: then the deliverable is the plan, not a
result. A file-only workspace does not by itself remove the client or harness's
external HTTP access. Workspace URLs under `https://api.hyperc.com/s/.../`
serve workspace files and capabilities; P34 calls use the separate API base
`https://api.hyperc.com/v1` and must never append `/fit` or `/result` to a
workspace URL. Write down the exact request
body you would send, the sequence (a `POST /fit` input test with `"mock": true`,
then a separately authorized real `POST /fit`, polling each returned session,
`DELETE /session/{id}` to cancel), where the key comes from on the host that
will run it, and an explicit **not executed** status against that request.

Two things that never follow from being unable to call:

- **Nothing is invented.** No session id, no status, no numbers, no "assume it
  succeeded", and no reuse of another request's session id as a placeholder —
  a record that says a fit ran is unfalsifiable to everyone downstream.
- **The checks in step 1 still run.** You cannot submit, but you can still
  validate the body you are handing on.

### 9. Keep one record per attempt

Whatever format the caller wants, it holds, per attempt: which request, the
session id or an explicit none, whether it was a mock or a real fit, the
statuses observed in order, the terminal status, whether its numbers are
predictions, and what the diagnostics said. Attempts that failed and attempts
that never ran are rows in it like any other — they are the rows a reader has
no other way to learn about.
