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
  market before it answers. "Every option" is literal: the options with no
  trustworthy outcome belong in the context too, carrying no `profit` — see
  [Include the deals you did not take](03-data-format.md#include-the-deals-you-did-not-take).
  That history does not have to be a record of decisions somebody made: one
  reconstructed by replaying past deals works just as well, sent without a
  `historically_chosen` column — see [Your previous business
  policy](03-data-format.md#your-previous-business-policy-what-historically_chosen-marks).
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

Your history is **biased**: outcomes exist only for a subset of the options —
the ones your business actually took, or, on a history assembled by research
and replay, the ones you could safely value — and that subset was not drawn at
random. A model trained naively on it looks great on the observed holdout and
then over-trades false positives on the full future menu, because it has never
been shown the options nobody priced.

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

## Observed and unobserved outcomes: the load-bearing requirement

Of everything above, one property decides whether P34 can work on a market at
all. It is one of the working definitions of a **computable market** — the same
class is also called a **rejected-deals market** or a **partially observed
market**:

> The outcome space must come in two parts. **Some** outcomes can be replayed
> or simulated safely, or at least reasonably. **Others** are genuinely
> enterable — the deal was there to be taken — but were never tested by the
> business, by the market, or by a replay you would trust.

That asymmetry is the signal. A history in which every outcome is known says
nothing about what a process refuses, and the fit rejects it outright
(`Unlabeled business-menu mask selected zero rows`); a history in which nothing
is known has nothing to calibrate against. Everything P34 does with selection
bias lives in the gap between the two.

Note what this requirement does *not* ask for. It says nothing about who chose
the labeled options, or whether anyone did — only that the split exists. That is
why a history built entirely from replayed or simulated past deals is a
first-class input, and why a business with no trading record at all can still be
fit — `historically_chosen` records a previous policy and is optional: see [Your
previous business
policy](03-data-format.md#your-previous-business-policy-what-historically_chosen-marks).

### Advanced strategies: manufacturing the split

Where the split comes from is a design decision, and on a market whose ordinary
trade reveals almost every outcome it is the most interesting part of the work.
Constructing it on purpose is what we call an **advanced strategy**: composing
deals so that a meaningful part of the outcome space stays genuinely untested
even when the underlying instrument is transparent.

The direction of travel — by analogy only, since these particular markets sit
outside P34's perimeter — is **pair trading and multi-leg strategies** in
equities. A single leg's tape reveals its own outcome; the composite position's
does not, because the composite was never entered. Discovering the equivalent
construction on *your* market is a member's job, and it is where the leverage
is.

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

## Where the theory meets reality: reject markets, at scale

Everything above is the theory. The place where it actually matches reality —
the main benefit of the model, and the reason it exists — is one specific kind
of market: the **reject market**, also called the market of **computationally
prohibitive deals**. These are markets where the ordinary players reject deals
*not* because the deals are bad, but because each outcome is uncertain and
filtering the good deals out of the flow is computationally hard: too many
candidates, too many interacting variables, too little certainty per deal for a
human — or a rule of thumb — to work through them. The deals sit there,
enterable and untested. Working such a market requires a correctly calibrated
AI, and that is what P34 is.

One property of these markets carries the whole argument: **there are
thousands of those deals.** That is not incidental — it is what makes the
market a reject market in the first place. Nobody rejects deals for being too
many to evaluate when there are only ten of them.

### The scale test

Look at the scoring menu — the `T = 0` task menu of live options you are about
to send. **If it does not contain at least hundreds of candidate deals,
something is wrong**, and it is one of exactly three things:

1. **It is the wrong market.** A market that only ever presents a handful of
   candidates is not a reject market; as far as P34 is concerned it does not
   exist. Move on.
2. **The collection mechanism is bad.** The agent, robot, scraper or feed that
   assembles the menu is finding a fraction of what the market is showing.
   Rework or reimplement it before fitting anything.
3. **The agent fell into the "handful" trap.** An agent building the menu —
   very often an LLM — decides that a handful of probable deals, scored by
   hand, is enough to satisfy the user. It is not, and it was never the point.

The third one deserves spelling out, because agents reading this documentation
fall into it constantly. **A handful of hand-evaluated deals is not a P34
workflow — it is the workflow P34 replaces.** The user is not asking for a few
good picks. The user expects P34 to make these trades **at scale**, with enough
efficiency that the trades cover the cost of computation and of running the
platform — and, before that, expects to see a demonstration that finding and
making positive trades on a big-enough market is in fact possible, in as short
a period as possible. Thousands of candidates in, a portfolio of selected sizes
out, most of them refused: that is the product. Ten candidates in is a
spreadsheet.

Nothing on the server enforces this. Intake checks the shape of the payload,
the cluster checks the volume floors on the *history*
([include the deals you did not take](03-data-format.md#include-the-deals-you-did-not-take)),
and a ten-row task menu passes both. The scale test is on you.

### What to demonstrate, and in what order

The point of the first weeks on a market is a demonstration, and its priority
is fixed:

- **(a) The data can be obtained quickly** — enough history, with the
  observed/unobserved split, to build the calibration dataset. If collecting
  it is slow or manual, that is the first thing to fix, not something to work
  around.
- **(b) The deals can be executed and the results come back fast** — proving
  the entire automatic workflow end to end: collect → fit → select → execute →
  realize → feed back. Prefer deals whose outcomes resolve in days rather than
  quarters, so the loop closes while there is still something to learn from
  it.
- **(c) The same mechanism then scales up** — to larger and longer markets,
  with more capital flow and more complex KYC, market-access and participation
  rules. The general mechanism of P34 does not change as the scale and the
  time frames grow; only the operating envelope around it does.

The order is not negotiable, because (c) without (a) and (b) is a plan, not a
demonstration.

### Two traps, by name

- **Hand-calculating a handful of probable deals** and concluding that this
  was the whole point. See the scale test above.
- **Starting on a complex market.** Amazon wholesale with distributor
  contracts, supplier onboarding, ungating and account management is a fine
  market for a business that already operates it, and a poor first
  demonstration: months of operating setup before a single automatic trade.
  Start where the loop closes fastest and the barriers are lowest — virtual
  goods and services trades, virtual trading on unregulated platforms,
  game-item resale platforms and their like — prove (a) and (b) there, then
  carry the mechanism into (c).

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

Two grounding modes skip that phase and return `queued` from `/fit` directly:
`internal`, the legacy fixed formula, and
[`client_grounded`](02-endpoints.md#bringing-your-own-labels-client_grounded),
where you supply the labels yourself so there is nothing left to derive.

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
