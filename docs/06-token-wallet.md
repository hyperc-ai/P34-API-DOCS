# 6. Token wallet: the plan account, the accumulating account, transfers and the ledger

Two places pay for a calculation, in this order:

1. **The plan account** — this week's plan credits, a membership's
   allowance. Your plan account is refilled every Monday at 00:00 UTC to your
   plan's weekly amount and is spent first. The weekly amount is a quarter of
   your plan's monthly grant, doubled while the account holds the
   [founding membership](#founding-membership-2-plan-credits); the refill tops
   the plan account up **to** it, never above, so nothing builds up there.
   What your plan grants is stated on the plans page and returned by
   `GET /account/balance` (`accounts.plan` and `plan_credits` for this week,
   `monthly_grant` for the month); it is not restated here, because it
   changes. Unused plan credits lapse at the weekly refill. Members who held a
   paid plan before 2026-11-04 keep the earlier rule until 2026-12-21: until
   then their unused plan credits still move into their accumulating account.
   See [the weekly lapse](#the-weekly-lapse) below.
2. **The accumulating account** — your token balance. Your accumulating
   account keeps everything else — top-ups, credits sent to you, your welcome
   credit, earlier carry-overs, sale proceeds and refunds — and does not
   expire. It is spent after the plan account. Credits never convert to cash.
   **Any account can buy tokens** in the
   [management console](https://api.hyperc.com/app/), with or without a
   membership, and bought tokens **never expire**. An account without a
   membership simply pays as it goes: register (free), buy tokens, call the
   API. The console states the price and the purchase bounds before you pay;
   the bounds also come back from `GET /account/balance` as `pay_as_you_go`.

* Every charge — model calls, the compute and runtime metered to your jobs,
  the sibling services your workflows use (data gateway, proxies,
  enrichment), and the markets you buy in the Market Store — is paid the same
  way: the plan account first, the accumulating account after (on the Invite
  tier, Market Store purchases are paid from the accumulating account only:
  `accounts.plan.market_usable`). With nothing
  left to pay with, calls are refused with `429` until next Monday's plan
  credits, a purchase, or an incoming transfer — see
  [budget errors](#budget-errors-429).
* Tokens in the accumulating account are **transferable** between accounts
  by email. Plan credits never sit there, so they cannot be transferred.
* The weekly window still exists, but only as a **burst bound** — it throttles
  how fast an account can spend (the console shows it as a meter) and takes
  no tokens away. A purchase opens matching headroom in it at once.

Every movement — what your calculations and services cost, what the week's
plan credits paid for, purchases, transfers in and out, grants, and Market
Store purchases, sales and refunds — is one row in an append-only **ledger**
you can read from the API and browse in the
[management console](https://api.hyperc.com/app/) (dashboard → *Plan account
& accumulating account* → *Full ledger*). The balance **is** the ledger sum;
there is no hidden state.

### The weekly lapse

Unused plan credits lapse at the weekly refill. Members who held a paid plan
before 2026-11-04 keep the earlier rule until 2026-12-21: until then their
unused plan credits still move into their accumulating account.

> **Changed 2026-11-04.** For an account whose paid plan begins on or after
> 2026-11-04, unused plan credits lapse at the end of their Usage Week, from
> the week that began on 2026-11-02: the first refill at which they lapse is
> the one of 2026-11-09 00:00 UTC. `lapse_from` is now the account's own.
>
> **Changes 2026-12-21.** From 2026-10-21 until 2026-12-21, the unused plan
> credits of members who held a paid plan before 2026-11-04 move into the
> token balance at the end of their week (ledger kind `grant`, from
> `plan-rollover`). From the week starting 2026-12-21 they lapse again.
> Tokens already on the balance stay; nothing is restated.

Which rule applies is a property of the account:

* **An account whose paid plan begins on or after 2026-11-04** — every
  Usage Week's unused plan credits lapse at its end, from the week that
  began on 2026-11-02 (the Usage Week that holds 2026-11-04).
* **A member who held a paid plan before 2026-11-04** (the members HyperC
  notified on 2026-11-04) — their Usage Weeks that end on or before
  2026-12-21 keep the earlier rule: their unused plan credits move into the
  accumulating account when the week ends. The first of their weeks whose
  unused plan credits lapse is the one that **starts** on 2026-12-21.

Nothing that has already moved into the accumulating account is taken back.
The API Terms of Use state the rule (§§1.25, 6.1, with the notice of §6.5).
`GET /account/balance` says which rule applies to your account in the current
week (`plan_credits.accumulates`, `plan_credits.lapses`) and from when
(`plan_credits.lapse_from`, the account's own), so a client never needs to
hard-code either date.

> **Changed 2026-10-05.** From 2026-08-21 until then, a plan's monthly grant
> was credited to the balance once a month and unused tokens carried over.
> Those monthly accruals have stopped — the allowance now arrives as weekly
> plan credits — but every token already credited stays on your balance;
> nothing was restated. Calling the API no longer needs a subscription.

## Founding membership: 2× plan credits

Founding members receive **twice** their plan's grant — the monthly figure,
and with it every week's plan credits — for as long as they hold the plan.
Founding status is assigned by **paid-registration order**: the first 1,000
accounts to pay for a membership (buying tokens alone does not enter the
ladder), the same ladder that locks their introductory success-fee rate. It
is a property of the account, so it does not lapse while your subscription
runs, and every wallet response tells you where you stand:

```json
{ "founding": true, "founding_multiplier": 2, "monthly_grant": 400.0 }
```

## Token amounts and exact units

Balances, plan credits, transfers and charges are quoted in **tokens** — the
unit you buy and your plan grants. Internally P34 counts in whole **units**,
8,000 to the token, which is what lets a single small calculation cost a
fraction of a token without rounding. Every amount therefore appears twice:

| field | meaning |
| --- | --- |
| `balance`, `available`, `plan_credits.weekly` / `.used` / `.left`, `accounts.plan.cap` / `.used` / `.left`, `accounts.accumulating.balance` / `.reversal_debt`, `amount`, `monthly_grant`, `tokens_charged` | tokens — what you are sold and what the console shows |
| `balance_units`, `available_units`, `plan_credits.weekly_units` / `.used_units` / `.left_units`, `accounts.plan.cap_units` / `.used_units` / `.left_units`, `accounts.accumulating.balance_units` / `.reversal_debt_units`, `amount_units`, `monthly_grant_units`, `tokens_charged_units` | the exact internal integer, never rounded |
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

An example — a founding member who held a paid plan before 2026-11-04,
partway through the Usage Week beginning 2026-12-21, the first of their weeks
whose unused plan credits lapse:

```json
{
  "plan": "base",
  "balance": 396.875,
  "balance_units": 3175000,
  "plan_credits": {
    "mode": "weekly",
    "week": 2972,
    "weekly": 100.0,
    "weekly_units": 800000,
    "used": 12.5,
    "used_units": 100000,
    "left": 87.5,
    "left_units": 700000,
    "replenishes_at": "2026-12-28T00:00:00+00:00",
    "accumulates": false,
    "lapses": true,
    "lapse_from": "2026-12-21T00:00:00+00:00"
  },
  "available": 484.375,
  "available_units": 3875000,
  "monthly_grant": 400.0,
  "monthly_grant_units": 3200000,
  "founding": true,
  "founding_multiplier": 2,
  "units_per_token": 8000,
  "accounts": {
    "plan": {
      "plan": "base",
      "left": 87.5, "left_units": 700000,
      "cap": 100.0, "cap_units": 800000,
      "used": 12.5, "used_units": 100000,
      "refills_at": "2026-12-28T00:00:00+00:00",
      "week": 2972,
      "lapses": true,
      "lapse_from": "2026-12-21T00:00:00+00:00",
      "market_usable": true
    },
    "accumulating": {
      "balance": 396.875, "balance_units": 3175000,
      "reversal_debt": 0.0, "reversal_debt_units": 0
    }
  }
}
```

For an account whose paid plan began on or after 2026-11-04, this week —
like every week of its plan — reads `"accumulates": false`, `"lapses": true`
and `"lapse_from": "2026-11-02T00:00:00+00:00"`.
The response also carries `pay_as_you_go`, described below.

* `plan_credits` — the plan account this Usage Week: `weekly` (a quarter of
  `monthly_grant`; 0 without a membership), `used`, `left`, and
  `replenishes_at` — next Monday 00:00 UTC, when the plan account is refilled
  to `weekly`. `week` numbers the Usage Week; `mode` is `weekly`.
  `accumulates` is `true` while this week's unused plan credits will move
  into the accumulating account at its end (for a member who held a paid
  plan before 2026-11-04, every week before 2026-12-21, on every plan but the
  Invite tier, whose plan credits never carry over; for an account whose paid
  plan began on or after 2026-11-04, no week); `lapses` is `true` when they
  lapse at the refill instead. `lapse_from` is the account's own: when the
  lapse starts for this account — the start of its first lapsing week as an
  ISO time (`2026-12-21T00:00:00+00:00` for a member who held a paid plan
  before 2026-11-04, `2026-11-02T00:00:00+00:00` for an account whose paid
  plan began on or after 2026-11-04), `"always"` when every week lapses, or
  `null` while every week carries over. Two accounts can read different
  values in the same week; read your own rather than assuming one date.
* `balance` — the accumulating account (the token balance): purchases,
  transfers in, grants, the tokens credited by monthly accruals before
  2026-10-05 and by weekly carry-overs under the earlier rule
  ([the weekly lapse](#the-weekly-lapse)), Market Store sale proceeds and
  refunds. It is spent after the week's plan credits, and a
  post-paid service charge can take it below zero (the `service` ledger
  entries below).
* `available` — `plan_credits.left` plus `balance`: what the next calculation
  can draw on. Check this rather than `balance` before submitting work — a
  member's balance can sit at zero while the week's plan credits still pay.
* `accounts` — the same two accounts by name. `accounts.plan` is the plan
  account: `left`, `cap` (the weekly amount), `used`, `refills_at`, `week`,
  `lapses`, `lapse_from`, and `market_usable` — whether its plan credits may
  pay for Market Store purchases (every plan but the Invite tier's). Its
  `lapses` and `lapse_from` are those of `plan_credits` above: this account's
  own rule, which can differ from another account's in the same week.
  `accounts.accumulating` is the accumulating account: `balance`, and
  `reversal_debt` — the part of a negative balance left by a reversed Market
  Store sale (below). `accounts.accumulating.balance` equals `balance`; `plan`
  is still the plan code.
* `pay_as_you_go` — `{"enabled", "min_topup_usd", "max_topup_usd"}`: whether
  the console sells pay-as-you-go tokens and the bounds of a single purchase,
  in whole US dollars. Read the bounds here rather than hard-coding them.

Reading the balance (or the ledger) also settles what is due first, so the
numbers are always current. A negative balance is paid down from the next
week's plan credits — except a debt left by a reversed Market Store sale,
which only later proceeds, transfers or purchases pay down. The wallet
endpoints authenticate your key but **never require anything to pay with** —
an empty account can still read its balance and ledger, and receive tokens.

## `GET /account/ledger` — the full query-able ledger

Newest first. The page opens with the same wallet fields as
`GET /account/balance` (shortened below); each entry carries **time, from, to,
amount, msg** plus bookkeeping fields:

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
    { "id": 1207, "time": "2026-12-22T09:15:40+00:00", "kind": "grant",
      "from": "market-sales", "to": "you@example.com",
      "amount": 6.3, "amount_units": 50400,
      "msg": "Market sale proceeds",
      "direction": "in", "session_id": null, "account_part": "accumulating" },
    { "id": 1203, "time": "2026-12-22T08:01:12+00:00", "kind": "plan_credit",
      "from": "plan:base", "to": "you@example.com",
      "amount": 2.0, "amount_units": 16000,
      "msg": "weekly plan credits: Market Store: “Used e-bike arbitrage, Berlin” (community-…) ×2",
      "direction": "in", "session_id": null, "account_part": "plan" },
    { "id": 1202, "time": "2026-12-22T08:01:12+00:00", "kind": "purchase",
      "from": "you@example.com", "to": "market",
      "amount": 2.0, "amount_units": 16000,
      "msg": "Market Store: “Used e-bike arbitrage, Berlin” (community-…) ×2",
      "direction": "out", "session_id": null, "account_part": "accumulating" },
    { "id": 913, "time": "2026-10-06T14:02:11+00:00", "kind": "plan_credit",
      "from": "plan:base", "to": "you@example.com",
      "amount": 0.61725, "amount_units": 4938,
      "msg": "weekly plan credits: fit input: 12345 cells @ High (test key)",
      "direction": "in", "session_id": "a1b2c3…", "account_part": "plan" },
    { "id": 912, "time": "2026-10-06T14:02:11+00:00", "kind": "usage",
      "from": "you@example.com", "to": "p34:model",
      "amount": 0.61725, "amount_units": 4938,
      "msg": "fit input: 12345 cells @ High (test key)",
      "direction": "out", "session_id": "a1b2c3…", "account_part": "accumulating" },
    { "id": 907, "time": "2026-08-21T13:58:40+00:00", "kind": "transfer",
      "from": "you@example.com", "to": "teammate@example.com",
      "amount": 3.125, "amount_units": 25000,
      "msg": "seed the trading account", "direction": "in|out", "session_id": null,
      "account_part": "accumulating" },
    { "id": 811, "time": "2026-08-21T00:00:03+00:00", "kind": "accrual",
      "from": "plan:base", "to": "you@example.com",
      "amount": 400.0, "amount_units": 3200000,
      "msg": "monthly token accrual (plan grant, founding 2x)",
      "direction": "in", "session_id": null, "account_part": "accumulating" }
  ],
  "next_before": 811
}
```

* `kind` — `usage` (P34 model or metered runtime consumption, with the
  fit/predict `session_id` and a `msg` showing exactly how the charge was
  computed), `plan_credit` (what the week's plan credits paid for: written
  beside each charge they cover, for the amount covered, so a charge the
  week's credits cover in full leaves the balance where it was — as entries
  912 and 913, and 1202 and 1203, above do; also written when they pay down a
  negative balance, and, from your account, when a refund gives plan credits
  back to the week), `purchase` (a Market Store purchase, to `market`, and
  its refund back to you, from `market`), `topup` (a pay-as-you-go
  purchase), `service` (a sibling service charging what it used on your
  behalf — post-paid and idempotent, and paid from plan credits first like
  every charge; once those are spent it can take the balance below zero, and
  the next week's plan credits, a purchase or a transfer settles it),
  `transfer` (member to member), `grant` (credits granted to you; `from`
  names the source: `market-sales` — the proceeds of a Market Store sale of
  yours, or, with `direction: out`, the reversal of one; `plan-rollover` — a
  week's unused plan credits carried over under the earlier rule (for a
  member who held a paid plan before 2026-11-04, the weeks before
  2026-12-21);
  `market-welcome` — your welcome credit; `admin` — a service credit),
  `adjust` (bookkeeping, e.g. the wallet-launch carry-over), `accrual` (a
  monthly plan grant credited to the balance — how plans paid out until
  2026-10-05; earlier entries keep that kind).
* A market refund returns the plan part to this week's plan credits, up to
  what you used this week (a plan part beyond that lapses: it never reaches
  the balance); the rest of the refund goes to the balance.
* `from` / `to` — account **emails**, or a system party: `plan:<code>`,
  `p34:model`, `p34:runtime`, `svc:<service>`, `stripe` (purchases),
  `market` (Market Store purchases), `market-sales`, `plan-rollover`,
  `market-welcome`, `admin`, `migration`.
* `direction` — `in` (credit) or `out` (debit) from **your** point of view; a
  transfer appears in both parties' ledgers as the same entry with opposite
  directions.
* `account_part` — the account an entry belongs to: `plan` for a
  `plan_credit` entry (the plan account), `accumulating` for every other one
  (the token balance).

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
never overdraft, and only the balance moves — plan credits cannot be sent) ·
`422` invalid amount or self-transfer · `401` bad key.

The recipient does **not** need a membership to receive or spend the tokens:
an account without one pays as it goes, so transferred tokens are spendable at
once (the `base` plan's weekly burst bound applies) until its balance is
empty, at which point it gets the pay-as-you-go `429`
[below](#budget-errors-429). The console's dashboard has the same transfer
form under *Plan account & accumulating account*.

Market licenses move only in the Market Store, never with a token transfer
([12-market-store-api.md](12-market-store-api.md#trading-copies-the-order-book-offers)).

## How charges are computed (unchanged)

`units = cells × direction_price × effort_mult × key_mult`, rounded up to a
whole unit — inputs are cheaper than outputs, `market_type.effort` scales on
an exponential grid (Low … Unfair), and `profit-` keys carry a higher
multiplier than `test-` keys. The rates themselves are deliberately not
restated here, because they change: every charge's arithmetic is spelled out
in its ledger entry's `msg`, `/fit` reports what it charged in its `billing`
block (`tokens_charged` + `tokens_charged_units`), and dividing units by
`units_per_token` gives the token figure.

## Budget errors (`429`)

| situation | response |
| --- | --- |
| no membership, token balance empty | `429` `"token balance empty — this account has no subscription, so it pays as it goes: buy pay-as-you-go tokens … or subscribe to the P34 workspace membership for weekly plan credits"` |
| membership, this week's plan credits used up and the token balance empty | `429` `"token balance empty and this week's plan credits are used up — they replenish <next Monday> 00:00 UTC; to continue now, buy pay-as-you-go tokens …"` |
| a `/fit` whose estimated cost exceeds the plan credits left plus the balance | `429` `"estimated cost of this calculation (~… tokens) exceeds what you can pay with: … weekly plan credits left + a token balance of … — buy pay-as-you-go tokens …"` |
| weekly burst bound hit | `429` `"token budget exhausted (weekly burst window) — it resets automatically; a pay-as-you-go top-up opens matching headroom now …"` |

Every `429` body is flat — `{"detail": "…", "status": "failed"}` — so a client
polling `/result` stops waiting. The first three name the *token balance* on
purpose: read them as "pause until the account can pay" (a purchase, a
transfer in, or Monday's plan credits), not "retry shortly". A `429` never
loses data: nothing is enqueued or charged for the rejected call.
[`mock: true` input tests](02-endpoints.md#mock-mode-input-testing) remain
free and work with nothing to pay with, on every tier (with nothing to pay
with, within the free tier's limits — see
[request limits](02-endpoints.md#request-limits)).
