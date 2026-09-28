# Where inefficiency can be captured — the theory behind computable markets

In a market with no ticker and no order book, excess return has exactly two admissible sources: you produce the same outcome at a lower cost than the marginal participant, or you are right where the marginal participant is systematically wrong. Every persistent inefficiency the literature names is one of those two, and the seven reasons a deal gets rejected in practice — the reject-reason taxonomy behind the [catalogue](05-market-catalog.md) — sort cleanly between them.

This note is the theory behind the [candidate-markets waiting list](08-candidate-markets.md) and the "Where it pays" section of the [overview](01-overview.md#where-the-theory-meets-reality-reject-markets-at-scale).

## Two sources, one decomposition

The value of an action *a* to an operator *o* at size *q* is not its gross spread but what survives the operator's own costs and risks:

```
V(a, o, q) = G(a, o, q) − C_execution − C_operations − C_funding − E[L] − C_exit − ρ(a, o, q)
```

The cost terms carry the operator's index. Two operators can rationally assign different values to the same lot because their trucks, storage, capital and exit channels differ; this is comparative advantage, and it needs no forecast to exploit. The gross value *G* and the expected loss *E[L]* are estimates, and estimates are where other participants err. The size term *q* makes the action space combinatorial: a thin book or an ageing inventory turns one nominal deal into many economically distinct ones — which is why the Menus table carries [one row per quantity option](03-data-format.md#the-menus-table).

An efficient-markets reading (Fama, 1970) says neither source should survive. The literature since then explains why both do: information is costly to acquire, arbitrage is costly to execute, quality is hidden, attention is bounded, histories are selected, stock perishes, and size moves price. Each is a named mechanism with a named author, and each maps to a reject reason.

## Seven mechanisms that let an inefficiency persist

| Mechanism | Source | Why it survives competition | Side of the edge | Reject reason |
| --- | --- | --- | --- | --- |
| Costly information | [Grossman & Stiglitz, 1980](https://www.jstor.org/stable/1805228) | Prices cannot fully reflect information that costs money to gather; a fully efficient price would leave nobody paid to gather it, so an equilibrium degree of inefficiency remains | Be right | Attention, Complexity |
| Limits to arbitrage | [Shleifer & Vishny, 1997](https://doi.org/10.1111/j.1540-6261.1997.tb03807.x) | Closing a mispricing needs capital, a holding horizon and the capacity to execute; when execution means a truck, a cold room or a licence, the set of participants who can close it is small | Be cheaper | Operational fit, Capacity, Scale |
| Adverse selection and the winner's curse | [Akerlof, 1970](https://doi.org/10.2307/1879431); [Capen, Clapp & Campbell, 1971](https://doi.org/10.2118/2993-PA); [Thaler, 1988](https://doi.org/10.1257/jep.2.1.191) | With hidden quality, the winning bid is the most optimistic estimate; buyers who do not shade for it overpay, and sellers with private information sell as-is | Be right | Prediction |
| Bounded and rational inattention | [Simon, 1955](https://doi.org/10.2307/1884852); [Sims, 2003](https://doi.org/10.1016/S0304-3932(03)00029-1) | A decision-maker with finite processing capacity samples part of the menu and leaves the rest untested; the untested part is not priced at all | Be right | Attention |
| Selection-biased outcome histories | [Heckman, 1979](https://doi.org/10.2307/1912352); [Swaminathan & Joachims, 2015](https://jmlr.org/papers/v16/swaminathan15a.html) | Outcomes are observed only for actions the prior policy chose, so any model trained on them inherits that policy's optimism and over-enters when the menu widens; correcting for the bias is itself an edge | Be right | Prediction (the estimate, not the opportunity, was the defect) |
| Perishable inventory | [Arrow, Harris & Marschak, 1951](https://doi.org/10.2307/1906813) (newsvendor) | Unsold stock is worth zero after its window, so the decision is sizing under demand uncertainty; nobody can hold, and time-to-act is a cost the marginal participant cannot pay | Be cheaper | Time, Capacity |
| Market impact and strategy capacity | [Kyle, 1985](https://doi.org/10.2307/1913210); [Almgren & Chriss, 2001](https://doi.org/10.21314/JOR.2001.041) | Size moves price and consumes the remaining menu, so returns are capacity-constrained and the marginal unit is worth less than the first | Be cheaper | Scale, Capacity |

Four mechanisms are cost-side and are exploited by whoever can execute more cheaply; three are estimate-side and are exploited by whoever estimates better. Only the estimate side leaves a record of what was passed over — the declined rows in a decision history, the `historically_chosen = 0` rows of a [Menus table](03-data-format.md#include-the-deals-you-did-not-take) — and that record is what makes the second source learnable rather than merely arguable.

## What the theory predicts

**The two sides decay at different rates.** Attention is the cheapest inefficiency to remove: once evaluation costs fall, the untested part of the menu gets tested, and Grossman–Stiglitz predicts the residual shrinks toward the new cost of information. Estimate-side edges last while histories stay private and adverse selection stays uncorrected. Cost-side edges last as long as the marginal participant must own the physical or legal means of execution; Shleifer–Vishny limits do not move when models improve. The durable position is therefore a cost advantage the operator already holds, plus a model that reads it — not a model alone.

**Partial observability is a consequence, not a criterion.** When the asset is consumed — eaten, installed, soldered in, retired — the only true outcome is the sale to the end user or the write-off, and it arrives after the decision. Consumption therefore produces the delayed, path-dependent label that selection bias feeds on; it is why the [Sales table](03-data-format.md#the-sales-table) is an event tape and not a revenue total. It also removes supply, which is what stops open capital from competing the edge away; assets with a consumer are structurally less efficient than assets that are merely traded.

**Sizing is part of the estimate.** Because impact and capacity enter the value function through *q*, the question is never "is this deal good" but "at what size is this deal good for this operator". A model that predicts unit economics and treats quantity as an afterthought will be right on average and wrong at the margin that matters.

**The falsifiable statement.** For a market–operator pair where actions can be enumerated, outcomes attributed, constraints encoded and feedback repeated, a decision system fitted to the operator's own records should approach the best policy measurable from those records, and should beat the operator's prior policy mainly by declining false positives. The claim is weakened for a given market when no model beats a simple baseline after costs, when performance disappears once post-decision leakage is removed, when recommended actions rely on unsupported regions, or when the policy's own impact invalidates history faster than it can be refitted. No-free-lunch and no-arbitrage results still bind: compute cannot recover information the records never contained.

## Sources

The seven mechanisms link to their papers in the table. The decomposition and the computability conditions follow the [Computable Markets working paper](https://github.com/hyperc-ai/p34-technical-report); the reject-reason taxonomy is the [catalogue's](https://hyperc.com/markets.html); Fama, [Efficient Capital Markets, 1970](https://doi.org/10.2307/2325486).

*Version 2026-09-27. A research note: nothing here is a forecast of returns in any market.*
