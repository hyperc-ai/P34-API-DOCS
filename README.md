<div align="center">

<img src="https://hyperc.com/assets/img/og-card.png" alt="HyperC P34 — The Self-Driving Business AI Model" width="720">

# P34 API

**Your AI can talk. P34 lets it do business.**

[Website](https://hyperc.com) · [Markets catalogue](docs/05-market-catalog.md) · [Membership](https://hyperc.com/membership.html) · [Console](https://api.hyperc.com/app/) · [Simulator](https://api.hyperc.com/sim/) · [Research](https://hyperc.com/research.html) · [Technical report](https://github.com/hyperc-ai/p34-technical-report)

</div>

---

P34 is a **foundational decision model for computable markets**. This API answers one question:

> **Given the trade options in front of you right now — which should you take, at what size, and what profit should you expect?**

If your LLM is the voice of your business, P34 is its P&L. Language models reason in words; P34 is trained against realized economic outcomes (Profit-as-Regression Machine Learning, **PARML**). Ask it about a menu of deals and you don't get an essay — you get a portfolio: selected quantities, predicted profit, and — just as deliberately — the deals it refuses. **The refusals are the product.**

This repository is the complete user-facing documentation for the P34 API: how it works, how to prepare your data, runnable examples, and a pytest-based integration workflow.

## Addresses

| Service | URL | What it is |
| --- | --- | --- |
| **API** | `https://api.hyperc.com/v1/` | The P34 model API (`POST /fit`, `GET /result/...`) |
| **Management console** | `https://api.hyperc.com/app/` | Account, API keys, plans/billing, session status & cancel |
| **Market simulator** | `https://api.hyperc.com/sim/` | Interactive browser simulator — play a synthetic market with P34 predictions |

`GET https://api.hyperc.com/v1/` is open (liveness + capability listing); all
other API calls require an API key from the management console, sent as
`Authorization: Bearer <key>`, on an account with an **active subscription**
(subscribe on the console's plans page — there is no free usage tier).

## Is this for you?

- ✅ You face **menu-shaped decisions**: inventory purchasing, wholesale lots, loan approvals, load acceptance, contract sizing — many (item, quantity) options per decision moment.
- ✅ You have **history**, including the options with no outcome attached — or you're willing to start logging it. No trading record at all? A history assembled from market research and replayed past deals is a first-class input — see [what `historically_chosen` really means](docs/03-data-format.md#what-historically_chosen-really-means).
- ✅ You can measure an economic outcome: profit, contribution margin, recovery, yield.
- ✅ You want an executable answer — sizes and predicted economics — not a dashboard.
- ✅ You're wiring an **AI agent** (Claude, ChatGPT, open models, custom code) to real commercial decisions and need the one step it can't do alone.
- ❌ You need sub-second decisions (fits take minutes; very high-frequency use is out of scope).
- ❌ You want signals for securities, derivatives or prediction markets (regulated-market uses sit in a separate perimeter — see the [terms](https://api.hyperc.com/app/)).

## Why not just train a regressor on your history?

Your history is **biased**: outcomes exist only for a subset of the options — the ones your business actually took, or the ones a research-built history could safely value — and that subset was never drawn at random. A model trained naively on it looks great on the observed holdout — then over-buys false positives on the full future menu it was never forced to refuse.

| | Naive profit regressor | P34 |
| --- | --- | --- |
| Trains on | Deals you took (the winners' club) | The **whole menu**, including declined options |
| Backtest | Excellent (0.9266 AUC in our benchmark) | Honest |
| Full future menu* | **−$417.4k** realized | **+$2,250 on $4,146** deployed |
| "Do nothing" | Not in the vocabulary | A first-class, rewarded output |
| Portfolio | Per-row scores that fight for capital | Jointly sized book, calibrated as a sum |

\* Executed slower-market-waves notebook, synthetic market with known ground truth — mechanism demonstration, not evidence of live-market profitability. Methodology and notebooks: [p34-technical-report](https://github.com/hyperc-ai/p34-technical-report) and the [research page](https://hyperc.com/research.html). In production the model has generated **$30M+ in sales for customers with >95% of trades unsupervised** (company-reported; not audited by a human licensed auditor).

## The mental model

You send **two tables and a config**, and later receive **one predicted menu**:

- **Menus** — every trade option you faced, historically and right now. One row
  per *(key, quantity option)*. Historical menus are the model's **context**:
  P34 is pre-trained, so fitting on your history doesn't teach it markets from
  scratch — it calibrates the model to *your* market before it answers.
  "Every option" is literal: the options carrying **no** trustworthy outcome
  belong in the context too — the service **refuses a history in which every
  group is observed**. That two-part structure (some outcomes safely known,
  others enterable but never tested) is what makes a market computable in the
  first place — see [observed and unobserved
  outcomes](docs/01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement).
- **Sales** — your realized sales log. Used to *ground* the history: the service
  replays your inventory economics (holding costs, write-offs, fees) to
  reconstruct what every historical option would have earned.
- **market_type** — the grounding configuration describing those economics.
- **business_description** — your business and, crucially, **how its unit
  economics is computed**. Under the recommended
  [`business_led` grounding mode](docs/02-endpoints.md#grounding-modes) this
  text is compiled into the economics used to reconstruct your history, so it
  is executable input rather than documentation. You can send it per request
  or save it once in the console.

The **task** is the menu you want decided **now** (`T = 0`, `menu = 0`). The
response fills it in: per key, the selected quantity (`qty = 0` = *do not
trade*) and the predicted profit, calibrated as a portfolio sum. The task menu
must carry **no outcome values** — P34 never sees your future.

```
POST /fit  ──►  validation + grounding  ──►  queued
                                             │   (calculation runs on
                                             ▼    HyperC's compute cluster)
GET /result/{session_id}  ◄──  queued → processing → done | failed
```

By default, grounding is compiled from your business description and runs
*after* the response, so `/fit` answers `grounding` and the same poll loop
covers the extra phase:

```
GET /result/{session_id}  ◄──  grounding → queued → processing → done | failed
```

## Quickstart

Check the service is up (no key needed):

```bash
curl https://api.hyperc.com/v1/
```

Run the complete sample client (fit → poll → portfolio):

```bash
pip install pandas requests pyarrow
python examples/client/example_client.py --url https://api.hyperc.com/v1 --key $P34_API_KEY
```

Or call it directly:

```python
import requests
r = requests.post("https://api.hyperc.com/v1/fit",
                  headers={"Authorization": "Bearer <key>"},
                  json={"menus": [...], "sales": [...], "market_type": {...},
                        # your business + its unit economics (fees, holding
                        # costs, …); or save it once in the console instead
                        # and omit this field entirely
                        "business_description": "..."})
                        # grounding is compiled from that description by
                        # default; send "grounding_mode": "internal" for the
                        # legacy fixed formula
session = r.json()["session_id"]
# poll until done (business-led fits pass through "grounding" first):
requests.get(f"https://api.hyperc.com/v1/result/{session}",
             headers={"Authorization": "Bearer <key>"}).json()
```

No code? The [simulator](https://api.hyperc.com/sim/) runs a synthetic market
in your browser against this same `/v1` API — a good way to build intuition
for menus, grounding and portfolio behaviour before wiring your own data.

## Documentation map

1. [docs/01-overview.md](docs/01-overview.md) — what P34 does and the mental
   model behind the API (menus, sales, the T=0 task).
2. [docs/02-endpoints.md](docs/02-endpoints.md) — endpoint reference, auth,
   result statuses, model versions, confidence correction.
3. [docs/03-data-format.md](docs/03-data-format.md) — the Menus / Sales /
   market_type input format, rule by rule.
4. [docs/04-errors-and-checks.md](docs/04-errors-and-checks.md) — common
   validation errors and quick self-checks.
5. [docs/05-market-catalog.md](docs/05-market-catalog.md) — the computable
   markets catalogue: every market, its tier, its support state, its menu
   shape and the data it runs on.
6. [docs/06-token-wallet.md](docs/06-token-wallet.md) — the accumulating
   token wallet: monthly accruals that carry over (2,000 tokens a month, 4,000
   for founding members), transfers between accounts by email, and the full
   query-able ledger.
7. [examples/](examples/) — runnable code:
   - [examples/client/](examples/client/) — a complete sample client
     (fit → poll → portfolio).
   - [examples/data/](examples/data/) — sample input as Excel, CSV, and JSON.
   - [examples/pytest/](examples/pytest/) — a minimal pytest workflow you can
     drop into CI to validate your integration.
   - [examples/baseline_comparison/](examples/baseline_comparison/) — a demo
     that pits P34 against a gradient-boosting profit regressor on a synthetic
     market with known ground truth.

## Access & membership

API access comes with the **P34 Membership** — **$2,000/month**: a
**24/7 virtual machine** for your agent — an always-on workspace preloaded with
market-access tools, curated data sources and web scraping, so the agent can
collect data and operate the business continuously rather than only while you
are at the keyboard — plus the API, console and simulator, a weekly compute
allowance (shown as % used), access to computable markets — **the market you
already operate in** first, plus supported workflows where we have coverage
(Amazon wholesale, US & EU) — agent skills and examples, and a community of operators. Early paid accounts lock the
introductory **10% success-fee rate** where profit-share pricing applies —
assigned by paid-registration order and shown in your account.

**[Explore membership →](https://hyperc.com/membership.html)** ·
**[Join at the console →](https://api.hyperc.com/app/)** ·
Enterprise (governed rollout: shadow test → capped pilot → scale with controls):
**[hyperc.com/enterprise.html](https://hyperc.com/enterprise.html)**

## Market coverage

**[→ The computable markets catalogue](docs/05-market-catalog.md)** — 69 markets, six tiers,
each with a support state, menu shape and data sources. Read it before the industry cases:
it is the overview, they are the deep dives. Machine-readable copy for agents at
[hyperc.com/markets.json](https://hyperc.com/markets.json).

| Tier | What it is | Count |
| --- | --- | --- |
| **Core** | Institutional scale — wholesale, lending, cards, insurance, treasury, procurement | 19 |
| **Tier 1** | Cleanest telemetry, minimal handling — domain drops, vinyl, retro games, LEGO, TCG, sneakers | 10 |
| **Tier 2** | Strong fit, needs handling or local presence — tools, cameras, salvage, pallets, auctions | 18 |
| **Tier 3** | Digital and intangible — micro-acquisitions, plugins, stock assets, gift cards, points | 8 |
| **Tier 4** | Operational and local — vending routes, rentals, lead arbitrage, work arbitrage | 8 |
| **Flagged** | Textbook menu structure, real legal exposure — declined by policy | 6 |

Support states across the catalogue: **1 supported** (Amazon wholesale US & EU, in production
since 2023), **6 pilot-ready** (validated or in enterprise discovery — micro-lending, card
credit, bank onboarding, manager underwriting, online arbitrage), **53 research** candidates,
**9 not currently supported** (regulated perimeter or declined by policy).

Synthetic markets are open to every member through the [simulator](https://api.hyperc.com/sim/)
and this API. **Listing a market is not a claim of support** — check the state before you plan
around it, and run the [market-fit check](https://hyperc.com/markets.html#fit) on your own
market. Proposing a new one: [hyperc.com/contact.html?topic=market](https://hyperc.com/contact.html?topic=market).

### Which market should you choose?

> **Start from the market you already operate in, or one you know well.** Support state records
> where P34 has already been pointed — it is not a ranking and not a recommendation. What makes
> P34 work on a market is your data, your constraints and your operating knowledge, so a market
> you understand beats a market with a pre-built workflow.
>
> In particular, **do not default to Amazon wholesale because it is the developed one.** It is the
> founding deployment and the best-understood market in the catalogue, and it is also one of the
> hardest to enter — and the difficulty is not the model. Amazon account management (ungating,
> brand and IP complaints, performance metrics, suspension and reinstatement) and wholesale
> supplier relationships (winning authorised distributor accounts at all, minimums, credit terms)
> are demanding operating problems, and P34 solves neither of them.
>
> Treat the supported and pilot-ready entries as evidence that the method works, not as a shortlist
> to pick from.

## What P34 is *not*

- **Not a chatbot.** It doesn't converse; your agent does. P34 supplies the economic decision.
- **Not a trading-signal service.** Regulated-market uses (securities, derivatives, prediction markets) are excluded from profit-share pricing and gated under the [API Terms of Use](https://api.hyperc.com/app/).
- **Not investment advice.** Output is statistical decision support; you own the decisions, the execution, the capital and the results.
- **Not an uncontrolled bot.** Recommended deployment runs menu grounding → shadow test → capped pilot → scale, with caps, audit logs and kill switches.
- **Not magic.** It requires policy-selection signal (you had more options than you took), tolerates minutes of latency, and refuses work its validation can't stand behind.

*Built to pursue profit — not generate pretty answers.*

## Support

- **API, console & billing:** support@hyperc.com (include your account email and, for calculations, the session id)
- **Sales, partnerships, press:** info@hyperc.com · [contact form](https://hyperc.com/contact.html)
- **Careers:** careers@hyperc.com

---

© HyperC (CriticalHop Inc). This repository contains user-facing documentation
and examples only; sample data is synthetic. Benchmark results shown are from
controlled synthetic markets unless labeled otherwise; production figures are
company-reported. Historical results do not guarantee future outcomes.
