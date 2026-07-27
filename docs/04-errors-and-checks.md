# 4. Errors, fit-response fields, and quick self-checks

## Fit response fields

`POST /fit` returns immediately after grounding and enqueueing:

- `session_id` — use it to poll `/result`.
- `labeled_rows` / `unlabeled_rows` — sizes of the grounded context. If
  `labeled_rows` is 0, no historical group had an observed outcome — check
  that chosen rows carry `profit` values or that Sales cover your keys.
- `task_menu_rows` — how many T=0 option rows were received.
- `parse_report` — per-rule counts of dropped/ignored rows. A large
  `menus_rows_dropped_no_choice` usually means `historically_chosen` is
  missing or mis-filled.
- `model` — the model version this fit will run on.

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

Other statuses you may meet: **401/403** — missing/invalid API key, or a
feature your account isn't flagged for; **413** — request over your plan's
size cap; **429** — compute budget exhausted for the current window (see
utilization in the [management console](https://api.hyperc.com/app/)).

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
