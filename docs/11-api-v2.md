# 11. API v2 — the obvious trades fast, then deeper analysis

Base URL: **`https://api.hyperc.com/v2`** · interactive reference:
**`https://api.hyperc.com/v2/docs`**

v2 takes **exactly the v1 request** ([endpoints](02-endpoints.md),
[data format](03-data-format.md)) and answers in **updates**. It responds
first with the obvious solutions, fast. It then runs a deeper statistical
analysis of your market, which adds further trades as it completes. You can
act on the first portfolio while the analysis continues.

v1 is unchanged: one calculation, one answer. Pick v2 when a fast first
answer is worth more to you than waiting for the complete one.

## Endpoints

| Method & path | Purpose |
| --- | --- |
| `GET /` | Service info: the v2 model names this server offers, the endpoint list. |
| `POST /fit` | Same body as v1 `/fit`. Answers like v1, plus `api_version: "v2"`, `more_expected: true` and `poll` (the result path). |
| `GET /result/{session_id}` | The portfolio so far. Keep polling until `status` is `final` or `failed`. |
| `DELETE /session/{session_id}` | Stop further analysis. The portfolio served so far stays available as `final`. |
| `POST /validate`, `GET /health`, `GET /account/*` | Identical to v1. |

Authentication, keys, tokens and mock mode are the same as in v1.

## Statuses: polling does not stop at the first portfolio

| status | meaning |
| --- | --- |
| `grounding`, `queued`, `processing` | As in v1: no portfolio yet. |
| `partial` | A portfolio is ready (`menu` is present) and `more_expected` is `true`. Further analysis is running and may add trades, so **keep polling**. |
| `final` | The stopping state: **no further updates will be made**. `final_reason` is one of: `complete`; `stopped` (you stopped it); `budget_exhausted` (your wallet could not pay for further analysis); `incomplete` (a deeper step could not complete, so the portfolio holds what was available). |
| `failed` | Ended without any portfolio. `error_code` and `error` are exactly as in v1. If you stopped the fit before its first portfolio, the code is `fit_canceled`. |

`more_expected` is the only forward-looking statement. Whether further
updates follow, and how many, depends on the analysis. Poll on
`more_expected` rather than counting updates.

## The portfolio only grows

Every update is merged into the portfolio you already have:

- a trade, once served (`qty > 0`), is **never withdrawn or resized** by a
  later update, because you may already have acted on it;
- later updates only add trades for keys that no earlier update traded;
- each `menu` row carries `added_in_update` (`1`, `2`, …, or `null` for a key
  that is not traded);
- `update` is the number of updates so far, and `updated_at` is when the
  latest one landed;
- `updates` lists each update with its `new_trades` and
  `new_predicted_profit`;
- `n_selected` and `predicted_profit_sum` describe the whole portfolio so far.

```json
{
  "api_version": "v2", "status": "partial", "more_expected": true,
  "session_id": "…", "model": "default", "update": 1,
  "updated_at": "2026-10-16T18:02:11+00:00",
  "menu": [
    {"key": "A001", "menu": 0, "T": 0, "qty": 3.0, "profit": 42.7, "added_in_update": 1},
    {"key": "A002", "menu": 0, "T": 0, "qty": 0.0, "profit": 0.0, "added_in_update": null}
  ],
  "n_selected": 1, "predicted_profit_sum": 42.7,
  "updates": [{"update": 1, "at": "2026-10-16T18:02:11+00:00", "new_trades": 1,
               "new_predicted_profit": 42.7, "confidence_correction_applied": false}],
  "detail": "results so far; deeper analysis is running and may add trades — keep polling until status is \"final\""
}
```

## Stopping

`DELETE /v2/session/{session_id}` ends further analysis. The step that is
running is canceled, and the portfolio served so far becomes `final` with
`final_reason: "stopped"`. The **Stop** button on the session's row in the
console's *Calculations* panel does the same. Before the first portfolio, a
stop cancels the fit, as in v1.

## Confidence correction

Send `confidence_correction` exactly as in v1
([confidence correction](02-endpoints.md#confidence-correction)). Not every
analysis step supports it yet, so the result tells you which ones applied it:

- `confidence_adjustment.applied_in_updates` lists the updates that applied
  it, and `not_applied_in_updates` lists those that selected their trades
  without it;
- the paired `qty±N` / `profit±N` columns appear once an update supports
  them, and an update that did not apply the correction contributes the same
  decision to every column;
- each column is merged by the same rule as `qty`: a trade is never
  withdrawn, only added to;
- `confidence_sweep` totals the merged columns, and its `threshold` is `null`
  because the portfolio was not cut at a single threshold.

## Cost

Every analysis step is billed for the compute it uses when it finishes, like
a v1 fit. A step canceled by a stop is not charged. Before each further step
the wallet is checked; if it cannot pay for that step, the session ends
`final` with `final_reason: "budget_exhausted"`.

## Mock mode and limits

- `"mock": true` works as in v1 and simulates the updates on the
  `mock_result_seconds` timer. Free keys may run mock fits on v2.
- Partner-market fits, and the markets available for actual free workspace
  fits, answer on `/v1/fit` only for now.
- A v1 `GET /v1/result/{session_id}` of a v2 session shows the first update
  only, and says so with `v2_session: true`.

## A client loop

```python
import time, requests

BASE = "https://api.hyperc.com/v2"
HEADERS = {"Authorization": "Bearer <key>"}

session_id = requests.post(f"{BASE}/fit", headers=HEADERS, json=body).json()["session_id"]
seen = 0
while True:
    res = requests.get(f"{BASE}/result/{session_id}", headers=HEADERS).json()
    if res["status"] in ("partial", "final") and res["update"] > seen:
        new = [row for row in res["menu"]
               if row["added_in_update"] and row["added_in_update"] > seen]
        place_orders(new)            # act on the new trades now
        seen = res["update"]
    if res["status"] in ("final", "failed"):
        break
    time.sleep(15)
```
