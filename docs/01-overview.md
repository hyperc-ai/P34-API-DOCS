# 1. Overview — what P34 is and how to think about it

P34 answers one question: **given the trade options in front of you right now,
which should you take, at what size, and what profit should you expect?**

It is built for *menu-structured* decisions — inventory purchasing, wholesale
lots, contract sizing, any setting where at each decision moment you face a
menu of (item, quantity) options, historically picked some of them, and later
observed what the picks earned.

## The mental model

You send **two tables, a config, and a business description**, and later
receive **one predicted menu**:

- **Menus** — every trade option you faced, historically and right now. One row
  per *(key, quantity option)*. Historical menus are the model's **context**:
  P34 is pre-trained, so the fitting done on your history does not teach it
  markets from scratch — it statistically calibrates the model to *your*
  market before it answers. "Every option" is literal: the deals you
  *declined* belong in the context too, with no outcome attached — see
  [Include the deals you did not take](03-data-format.md#include-the-deals-you-did-not-take).
- **Sales** — your realized sales log. Used to *ground* the history: the
  service replays your inventory economics (holding costs, write-offs, fees)
  to reconstruct what every historical option would have earned.
- **market_type** — the grounding configuration describing those economics.
- **business description** — free text describing the business *and how its
  unit economics is computed* (fees, accumulated costs, holding costs;
  approximations are fine). Sent per request, saved once in the console, or
  reused from the last fit — but a fit must resolve to one; see
  [Business description](02-endpoints.md#business-description). Under the
  default [`business_led` grounding
  mode](02-endpoints.md#grounding-modes) this text is **compiled into the
  economics that reconstruct your history**, so it is the highest-leverage
  field in the request.

The **task** is the menu you want decided **now**. It is marked two ways at
once, and both must agree: `T = 0` and `menu = 0`. Menu id `0` is reserved for
the task; every historical menu must use a non-zero id.

The response fills in the task menu: for each key, the selected quantity
(`qty = 0` means *do not trade*) and the predicted profit.

## Why not just a regressor?

Your history is **biased**: you only observed outcomes for the options your
business actually took, and your business took them *selectively*. A model
trained naively on that history looks great on business-observed holdouts and
then over-trades false positives on the full future menu — it has never seen
the options you (wisely) declined.

P34's principles, at the level relevant to a user:

1. **Profit-as-regression with selection awareness.** P34 does not treat the
   labeled history as an unbiased sample. It uses the *whole* menu — including
   the options you didn't take, availability flags, and your choice pattern —
   as signal.
2. **Grounded economics.** Instead of trusting a single `profit` number, P34
   can replay each historical decision through your market's economics (sales
   trajectory, holding costs, write-off horizon, fees) so that every option's
   counterfactual value is computed consistently.
3. **Risk-calibrated portfolio.** The returned selection is calibrated as a
   *sum*: take the `qty > 0` rows together as the recommended book, with the
   predicted total profit as its expectation.
4. **No ground truth in, none needed.** The task menu must not carry outcome
   values (the API rejects them). P34 never sees your future — the prediction
   pipeline holds no "actual" values at all.

See it in action against a naive regressor:
[examples/baseline_comparison/](../examples/baseline_comparison/).

## Why it works here: computable markets are *business* markets

P34 targets **computable markets**, and the reason the approach works on them
is that these are **business markets** — markets whose inefficiency exists
**by design**. A wholesale channel, a procurement program, a liquidation
pipeline: these are places where a business is *supposed* to capture a margin
by operating well. Markets like NASDAQ or the currency exchanges are the
opposite kind of place — markets where, in general, people are **not supposed
to do business** in that sense, and they are **not supported** by P34.

The distinctions run along four dimensions:

1. **A process, not a ticket.** On a computable market the business has to
   *operate a process* — sourcing, holding, fulfilling, collecting cash — and
   every business has its own specifics in how that process performs. The
   choices on the menu are therefore *specific to that business*: your MOQs,
   your lead times, your fee schedule, your risk appetite. On a regulated
   exchange the instrument is identical for every participant, and there is no
   operating process for a model to exploit.
2. **Inefficiencies persist.** The inefficiency P34 is designed to work in is
   expected to **persist over months and years** — it is structural, priced
   into how the market is organized. On exchanges, stocks, and forex, an
   inefficiency — even once discovered — is **very short-lived**: information
   is generally available, and any edge is easy to detect and exploit without
   a complex machine-learning / deep-learning system, so it is arbitraged away
   almost immediately.
3. **The data is honestly bad.** On P34-favored markets the data is **biased
   and only partially observed**, and the collectable features are typically
   **indirect signals** about the market — a sales rank, a stock-out flag, a
   category trend — rather than true volumes, order-book depths, the entire
   tape of deals traded by every player, plus the limit orders demonstrating
   every player's desires that an exchange publishes. P34 is built for the
   biased-and-partial regime (that is what the selection-aware fitting is
   for); exchange-grade transparency is precisely what makes exchange
   inefficiencies vanish.
4. **You already hold the menu.** Business decisions arrive as menus with a
   bounded option set per decision moment — which is what makes the market
   *computable* at all.

Which markets clear that bar in practice is catalogued in
[05-market-catalog.md](05-market-catalog.md) — 69 of them, from Amazon wholesale
and micro-lending down to expiring domain drops and local lead arbitrage, each
with its support state. Read that before the industry cases; it is the overview.

**Which one should you point P34 at? The market you already operate in**, or one
you know well. Support state records where P34 has already been pointed — it is
not a ranking and not a recommendation, and the model's usefulness on your market
comes from your data, your constraints and your operating knowledge, not from us
having shipped a workflow there. Note in particular that Amazon wholesale, the
one supported market, is also one of the *hardest to operate*: Amazon account
management and wholesale supplier relationships are demanding businesses in their
own right and sit entirely outside the model. Do not prioritise it because it is
the developed one. See
[Which market should you choose?](05-market-catalog.md#which-market-should-you-choose).

## Lifecycle of a request

```
POST /fit  ──►  validation + grounding  ──►  queued
                                             │   (calculation runs on
                                             ▼    HyperC's compute cluster)
GET /result/{session_id}  ◄──  queued → processing → done | failed
```

By default the grounding step is compiled from your business description and
runs after the response, adding one phase in front of the same poll loop:

```
POST /fit  ──►  validation  ──►  grounding (minutes, asynchronous)  ──►  queued
GET /result/{session_id}  ◄──  grounding → queued → processing → done | failed
```

Fits are **asynchronous**: `POST /fit` returns in seconds with a
`session_id`; the calculation itself typically takes minutes. Poll
`GET /result/{session_id}` (e.g. every 30 s) until `done`, or watch the
session live in the [management console](https://api.hyperc.com/app/), which
shows progress and lets you cancel.

## Try it without code

The **market simulator** at [https://api.hyperc.com/sim/](https://api.hyperc.com/sim/)
runs a synthetic market in your browser: configure demand and economics with
sliders (or load a pre-built scenario), step through decision weeks, and watch
capital evolve when trades follow P34's predictions. It speaks to the same
`/v1` API — a good way to build intuition for menus, grounding, and portfolio
behaviour before wiring your own data.
