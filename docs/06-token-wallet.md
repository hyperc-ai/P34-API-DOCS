# 6. Token wallet: accumulation, transfers, and the ledger

Since **2026-08-21** P34 token budgets are an **accumulating wallet**, not a
window that resets:

* Every monthly window, an account with an active paid plan is **credited its
  plan's monthly token amount** — **4,000 tokens** on the $2,000 plan currently
  sold, and **8,000** while your account holds the [founding
  membership](#founding-membership-2-tokens) — automatically, as a normal
  ledger entry.
* **Unused tokens carry over.** Nothing expires at the end of the month; a
  quiet month simply leaves the balance higher (missed months are
  back-credited when the account is next seen, up to 12 windows).
* Usage **debits the balance** — model calls, the compute and runtime metered
  to your jobs, and the sibling services your workflows use (data gateway,
  proxies, enrichment) all spend from the same wallet. When the balance
  reaches zero, calls are rejected with `429` until the next accrual, a plan
  upgrade, or an incoming transfer.
* Tokens are **transferable** between accounts by email.
* The weekly window still exists, but only as a **burst bound** — it throttles
  how fast the wallet can be spent (the console shows it as a meter), it no
  longer takes tokens away.

Every movement — monthly accruals, model consumption, transfers in and out,
service grants — is one row in an append-only **ledger** you can read from the
API and browse in the [management console](https://api.hyperc.com/app/)
(dashboard → *Token wallet* → *Full ledger*). The balance **is** the ledger
sum; there is no hidden state.

## Founding membership: 2× tokens

Founding members are credited **twice** their plan's monthly tokens — 400
instead of 200 on the base plan — for as long as they hold the plan. Founding
status is assigned by **paid-registration order**: the first 1,000 paying
accounts, the same ladder that locks their introductory 10% success-fee rate.
It is a property of the account, so it does not lapse while your subscription
runs, and every wallet response tells you where you stand:

```json
{ "founding": true, "founding_multiplier": 2, "monthly_grant": 400.0 }
```

## Token amounts and exact units

Balances, accruals, transfers and charges are quoted in **tokens** — the unit
the membership is sold in. Internally P34 counts in whole **units**, 8,000 to
the token, which is what lets a single small calculation cost a fraction of a
token without rounding. Every amount therefore appears twice:

| field | meaning |
| --- | --- |
| `balance`, `amount`, `monthly_grant`, `tokens_charged` | tokens — what you are sold and what the console shows |
| `balance_units`, `amount_units`, `monthly_grant_units`, `tokens_charged_units` | the exact internal integer, never rounded |
| `units_per_token` | the conversion factor (8,000) |

> **Changed 2026-08-21.** These fields used to carry the internal unit count
> directly — a 400-token balance read as `3200000`. The stored amounts are
> unchanged, so no history was rewritten; only the number you read moved. If
> your integration compares balances against a threshold, switch it to the
> `*_units` field or divide by `units_per_token`.

## `GET /account/balance`

```
curl -s https://api.hyperc.com/v1/account/balance \
  -H "Authorization: Bearer $P34_KEY"
```

```json
{
  "plan": "base",
  "balance": 396.875,
  "balance_units": 3175000,
  "monthly_grant": 400.0,
  "monthly_grant_units": 3200000,
  "founding": true,
  "founding_multiplier": 2,
  "units_per_token": 8000
}
```

Reading the balance (or the ledger) also materializes any accrual the account
is owed, so the number is always current. The wallet endpoints authenticate
your key but **never require a positive balance** — an empty account can
still read its ledger and receive or send tokens.

## `GET /account/ledger` — the full query-able ledger

Newest first. Each entry carries **time, from, to, amount, msg** plus
bookkeeping fields:

```
curl -s "https://api.hyperc.com/v1/account/ledger?limit=50" \
  -H "Authorization: Bearer $P34_KEY"
```

```json
{
  "plan": "base",
  "balance": 396.875,
  "balance_units": 3175000,
  "monthly_grant": 400.0,
  "founding": true,
  "units_per_token": 8000,
  "entries": [
    { "id": 912, "time": "2026-08-21T14:02:11+00:00", "kind": "usage",
      "from": "you@example.com", "to": "p34:model",
      "amount": 0.61725, "amount_units": 4938,
      "msg": "fit input: 12345 cells @ High (test key)",
      "direction": "out", "session_id": "a1b2c3…" },
    { "id": 907, "time": "2026-08-21T13:58:40+00:00", "kind": "transfer",
      "from": "you@example.com", "to": "teammate@example.com",
      "amount": 3.125, "amount_units": 25000,
      "msg": "seed the trading account", "direction": "in|out", "session_id": null },
    { "id": 811, "time": "2026-08-21T00:00:03+00:00", "kind": "accrual",
      "from": "plan:base", "to": "you@example.com",
      "amount": 400.0, "amount_units": 3200000,
      "msg": "monthly token accrual (base plan: 400 tokens, founding 2x)",
      "direction": "in", "session_id": null }
  ],
  "next_before": 811
}
```

* `kind` — `accrual` (monthly plan credit), `usage` (P34 model or metered
  runtime consumption, with the fit/predict `session_id` and a `msg` showing
  exactly how the charge was computed), `service` (a sibling service charging
  what it used on your behalf — post-paid and idempotent, so it can take the
  balance below zero; the next accrual or transfer settles it), `transfer`
  (member to member), `grant` (service credit), `adjust` (bookkeeping, e.g.
  the wallet-launch carry-over).
* `from` / `to` — account **emails**, or a system party: `plan:<code>`,
  `p34:model`, `p34:runtime`, `svc:<service>`, `admin`, `migration`.
* `direction` — `in` (credit) or `out` (debit) from **your** point of view; a
  transfer appears in both parties' ledgers as the same entry with opposite
  directions.

### Pagination

`?limit=N` (default 50, max 200) and `?before=<id>` cursor. `next_before` in
the response is the cursor for the next (older) page — `null` means you have
reached the end:

```python
entries, before = [], None
while True:
    page = api_get(f"/account/ledger?limit=200" + (f"&before={before}" if before else ""))
    entries += page["entries"]
    before = page["next_before"]
    if before is None:
        break
```

## `POST /account/transfer` — send tokens by email

```
curl -s -X POST https://api.hyperc.com/v1/account/transfer \
  -H "Authorization: Bearer $P34_KEY" -H "Content-Type: application/json" \
  -d '{"email": "teammate@example.com", "amount": 3.125, "msg": "seed the trading account"}'
```

```json
{ "transferred": 3.125, "transferred_units": 25000,
  "to": "teammate@example.com", "balance": 393.75, "balance_units": 3150000 }
```

* `email` — the recipient's **account email** (they must be registered).
* `amount` — **tokens**, positive; fractions are allowed (the smallest
  movement is one unit, 0.000125 tokens).
* `amount_units` — send an exact internal unit count instead; it wins when
  both are given.
* `msg` — optional note; it appears in both ledgers.

Errors: `404` unknown recipient email · `409` insufficient balance (transfers
never overdraft; any accrual due is credited before the check) · `422` invalid
amount or self-transfer · `401` bad key.

The recipient does **not** need an active plan to receive or spend the tokens:
a no-plan account holding transferred tokens may call the API (the `base`
plan's weekly burst bound applies) until its wallet is empty, at which point
it gets the usual *subscribe* rejection. The console's dashboard has the same
transfer form under *Token wallet*.

## How charges are computed (unchanged)

`units = cells × direction_price × effort_mult × key_mult`, rounded up to a
whole unit — inputs cheaper than outputs (0.1 / 0.4 units per cell),
`market_type.effort` on an exponential grid (Low … Unfair), `profit-` keys 10×
`test-` keys. Divide by 8,000 for the token figure: a 12,345-cell input at
High effort on a `test-` key costs 4,938 units = **0.61725 tokens**, so a
400-token month buys a lot of calculations. Every charge's arithmetic is
spelled out in its ledger entry's `msg`, and `/fit` reports what it charged in
its `billing` block (`tokens_charged` + `tokens_charged_units`).

## What changed for budget errors

| situation | response |
| --- | --- |
| no active plan, empty wallet | `429` `"no active subscription — subscribe to a plan to use the API"` |
| active plan, empty wallet | `429` `"token balance exhausted — tokens accrue monthly with your plan …"` |
| weekly burst bound hit | `429` `"token budget exhausted (weekly window) — it resets automatically …"` |

A `429` never loses data: nothing is enqueued or charged for the rejected
call. [Mock requests](02-endpoints.md#mock-mode-free-integration-testing)
remain free and work with an empty wallet.
