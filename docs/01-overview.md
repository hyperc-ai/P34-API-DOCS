# 1. Overview — what P34 is and how to think about it

P34 answers one question: **given the trade options in front of you right now,
which should you take, at what size, and what profit should you expect?**

It is built for *menu-structured* decisions — inventory purchasing, wholesale
lots, contract sizing, any setting where at each decision moment you face a
menu of (item, quantity) options, historically picked some of them, and later
observed what the picks earned.

## The mental model

You send **two tables and a config**, and later receive **one predicted menu**:

- **Menus** — every trade option you faced, historically and right now. One row
  per *(key, quantity option)*. Historical menus are the model's **context**:
  P34 is pre-trained, so the fitting done on your history does not teach it
  markets from scratch — it statistically calibrates the model to *your*
  market before it answers.
- **Sales** — your realized sales log. Used to *ground* the history: the
  service replays your inventory economics (holding costs, write-offs, fees)
  to reconstruct what every historical option would have earned.
- **market_type** — the grounding configuration describing those economics.

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

## Lifecycle of a request

```
POST /fit  ──►  validation + grounding  ──►  queued
                                             │   (calculation runs on
                                             ▼    HyperC's compute cluster)
GET /result/{session_id}  ◄──  queued → processing → done | failed
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
