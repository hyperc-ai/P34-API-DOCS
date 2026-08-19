<div align="center">

<img src="https://hyperc.com/assets/img/og-card.png" alt="HyperC P34 — The Self-Driving Business AI Model" width="720">

# P34 API

**Your AI can talk. P34 lets it do business.**

[Website](https://hyperc.com) · [Membership](https://hyperc.com/membership.html) · [Console](https://api.hyperc.com/app/) · [Simulator](https://api.hyperc.com/sim/) · [Research](https://hyperc.com/research.html) · [Computable Markets](https://computablemarkets.com) · [Technical report](https://github.com/hyperc-ai/p34-technical-report)

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
- ✅ You have **history**, including the options you *declined* — or you're willing to start logging it.
- ✅ You can measure an economic outcome: profit, contribution margin, recovery, yield.
- ✅ You want an executable answer — sizes and predicted economics — not a dashboard.
- ✅ You're wiring an **AI agent** (Claude, ChatGPT, open models, custom code) to real commercial decisions and need the one step it can't do alone.
- ❌ You need sub-second decisions (fits take minutes; very high-frequency use is out of scope).
- ❌ You want signals for securities, derivatives or prediction markets (regulated-market uses sit in a separate perimeter — see the [terms](https://api.hyperc.com/app/)).

## Why not just train a regressor on your history?

Your history is **biased**: you only observed outcomes for the options your business actually took, and it took them *selectively*. A model trained naively on that history looks great on business-observed holdouts — then over-buys false positives on the full future menu it was never forced to refuse.

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
  "Every option" is literal: the deals you *declined* belong in the context too —
  the service **refuses histories that are all wins**.
- **Sales** — your realized sales log. Used to *ground* the history: the service
  replays your inventory economics (holding costs, write-offs, fees) to
  reconstruct what every historical option would have earned.
- **market_type** — the grounding configuration describing those economics.

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
                        "business_description": "..."})
session = r.json()["session_id"]
# poll until done:
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
5. [examples/](examples/) — runnable code:
   - [examples/client/](examples/client/) — a complete sample client
     (fit → poll → portfolio).
   - [examples/data/](examples/data/) — sample input as Excel, CSV, and JSON.
   - [examples/pytest/](examples/pytest/) — a minimal pytest workflow you can
     drop into CI to validate your integration.
   - [examples/baseline_comparison/](examples/baseline_comparison/) — a demo
     that pits P34 against a gradient-boosting profit regressor on a synthetic
     market with known ground truth.

## Access & membership

API access comes with the **P34 Membership** — base tier **$200/month**: the
API, console and simulator, a weekly compute allowance (shown as % used),
supported-market workflows starting with **Amazon wholesale (US & EU)**, agent
skills and examples, and a community of operators. Early paid accounts lock the
introductory **10% success-fee rate** where profit-share pricing applies —
assigned by paid-registration order and shown in your account.

**[Explore membership →](https://hyperc.com/membership.html)** ·
**[Join at the console →](https://api.hyperc.com/app/)** ·
Enterprise (governed rollout: shadow test → capped pilot → scale with controls):
**[hyperc.com/enterprise.html](https://hyperc.com/enterprise.html)**

## Market coverage

- ✅ **Amazon wholesale — US & EU** — supported, in production since 2023
- ✅ **Synthetic markets** — simulator + API, open to every member
- 🟠 **Micro-lending** — validated in a ~3,000-loan live test; gated as regulated commerce
- 🟠 **Collectibles & online arbitrage** — research workflows, bring your own execution
- ⚪ **Freight, leads, capacity, and 40+ candidate markets** — research; see the
  [market-fit framework](https://hyperc.com/markets.html) and run the fit check on yours

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
