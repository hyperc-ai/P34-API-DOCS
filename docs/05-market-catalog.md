# Computable markets — the catalogue

**Read this before the industry cases.** This is the overview of every market HyperC
has identified as computable or as a candidate for computability; the
[industry cases](https://hyperc.com/cases.html) and the
[enterprise page](https://hyperc.com/enterprise.html) are the deep dives that follow it.

A market is **computable** when feasible actions can be enumerated as a menu, outcomes can
be attributed back to decisions, constraints can be encoded, and repeated feedback exists.
If your market clears that bar, P34 can be pointed at it — run the
[market-fit check](https://hyperc.com/markets.html) first.

> **Listing is not support.** Every entry carries a state. Most of this catalogue is
> `⚪ Research`: the structure fits and members are welcome to experiment, but there is no
> supported workflow yet. Do not read a listing as a claim that P34 ships that market today.

| State | Meaning |
| --- | --- |
| ✅ **Supported** | In production for members today. |
| 🟠 **Pilot-ready** | Validated or in active enterprise discovery; deployed under review. |
| ⚪ **Research** | Candidate market. Structure fits; member experiments welcome. |
| ⛔ **Not currently supported** | Declined by policy or held in a separate regulatory perimeter. |

**69 markets catalogued** · 1 supported · 6 pilot-ready · 53 research · 9 not supported.

Machine-readable copy for agents: **[hyperc.com/markets.json](https://hyperc.com/markets.json)**
(same catalogue, same ids, same states) and **[hyperc.com/llms.txt](https://hyperc.com/llms.txt)**.

## Which market should you choose?

**Not necessarily the supported one.** Choose the market you already operate in, or one you know well. Support state records where P34 has already been pointed — it is not a ranking and not a recommendation. The most developed market, Amazon wholesale, is also one of the hardest to enter: Amazon account management and wholesale supplier relationships are demanding operating problems that sit outside the model, and P34 does not solve them. What makes P34 work on a market is your data, your constraints and your operating knowledge, so a market you already understand beats a market with a pre-built workflow. Do not prioritise a market because we started there.

Practically: run the [market-fit check](https://hyperc.com/markets.html#fit) against the
market you already operate in or know well. If it clears the four criteria, that is your
market — bring its telemetry and constraints. Use the supported and pilot-ready entries as
evidence that the method works, not as a shortlist to pick from. Where a market carries a
**Hard to operate** note below, that difficulty is real and is not something P34 removes.

## Core markets

Institutional scale — the markets HyperC and its enterprise partners work directly. Large tickets, deep telemetry, and in several cases a live deployment behind them.

| Market | State | Notes |
| --- | --- | --- |
| **Amazon wholesale — US & EU** | ✅ Supported | The founding deployment: purchase and shipping portfolio decisions from live wholesale menus, in production since 2023 at roughly $100M/yr reseller scale (company-reported). <br>⚠️ *Hard to operate:* The best-understood market here and one of the hardest to operate — and the hard parts are not the model. Amazon account management (ungating, brand and IP complaints, performance metrics, suspension and reinstatement) and wholesale supplier relationships (winning authorised distributor accounts at all, minimums, credit terms) are demanding operating problems that P34 does not solve. Enter it because you already run it, not because it is the developed one. <br>*Menu:* SKU × quantity × supplier offer, with lead times and fees <br>*Data:* Supplier price lists, catalogue and fee data, sales velocity, returns |
| **Micro-lending — individual** | 🟠 Pilot-ready | Lend / no-lend calls where credit history is sparse or absent. About 3,000 loans issued in a live model test (2025). Regulated commerce: gated behind market-specific compliance review. <br>*Menu:* Applicant × offered principal × term <br>*Data:* Application attributes, repayment tape, collections outcomes |
| **Crypto transaction routing** | ⚪ Research | Routing and execution across venues in adversarial order flow. Deployed in research; a separate product and regulatory perimeter, not part of membership. <br>*Menu:* Route × size × venue, per transfer <br>*Data:* Venue depth, spread and fee telemetry, settlement latency |
| **Constrained FX invoice payments** | ⚪ Research | Which invoices to settle, in which currency and when, under liquidity and corridor constraints — a scheduling problem with a measurable cost of being wrong. <br>*Menu:* Invoice × corridor × settlement date <br>*Data:* Corridor rates and fees, liquidity positions, invoice ageing |
| **Casino customer incentivisation** | ⚪ Research | Offer selection and sizing scored on lifetime player economics rather than redemption rate, with abstention when the economics do not clear the bar. <br>*Menu:* Player segment × offer × value <br>*Data:* Play history, redemption and margin tape |
| **Prop trading risk management** | ⚪ Research | Allocation and limit decisions across traders and strategies. Financial perimeter: excluded from profit-share pricing and gated under the API Terms. <br>*Menu:* Trader/strategy × capital allocation × limit <br>*Data:* Realized P&L tape, drawdown and exposure history |
| **Manager underwriting — CLO / private credit** | 🟠 Pilot-ready | Manager selection as a menu decision under partial observability: candidate managers, sparse comparable histories, a measurable recovery target. Enterprise discovery case. <br>*Menu:* Candidate manager × commitment size <br>*Data:* Historical manager performance, recovery and default records |
| **Card overdraft and micro-loan offers** | 🟠 Pilot-ready | Limit increases, overdraft and micro-loan offers treated as one portfolio decision scored on expected lifetime economics. Designed for shadow evaluation against the incumbent policy first. <br>*Menu:* Cardholder × offer type × limit <br>*Data:* Balance and utilisation history, loss tape, incumbent policy decisions |
| **Bank customer onboarding** | 🟠 Pilot-ready | Onboarding incentives selected and sized on lifetime economics rather than conversion alone — refusing the offers that will not pay for themselves. <br>*Menu:* Prospect segment × incentive × value <br>*Data:* Onboarding cohorts, product uptake, lifetime margin |
| **Amazon discounter / online arbitrage at scale** | 🟠 Pilot-ready | Retail and online arbitrage run as a portfolio on public telemetry, pointed at small-ticket buyers rather than wholesale lots. <br>*Menu:* Discounted listing × quantity <br>*Data:* Keepa-class price and rank history, fee and returns data |
| **Alt-coin hedge fund** | ⛔ Not currently supported | Structurally a menu problem, but a financial-market perimeter. Excluded from membership and from profit-share pricing. <br>*Menu:* Asset × position size × horizon <br>*Data:* Venue price history, liquidity and flow telemetry |
| **Exotic asset hedge fund** | ⛔ Not currently supported | Illiquid and non-standard asset selection. Same perimeter and same exclusion as the above. <br>*Menu:* Asset × allocation <br>*Data:* Sparse comparable sales, holding-cost and carry data |
| **MCA — merchant cash advance (B2B)** | ⚪ Research | Advance / decline and sizing against future receivables, where the historical book is severely selection-biased — the failure mode P34 is built for. <br>*Menu:* Merchant × advance amount × factor rate <br>*Data:* Processing volume history, repayment and default tape |
| **Partial payment acceptance (bank)** | ⚪ Research | Which partial settlements to accept on delinquent balances, and at what discount — a recovery-maximisation menu, not a collections script. <br>*Menu:* Account × settlement offer × discount <br>*Data:* Delinquency ageing, historical recovery outcomes |
| **Prediction markets** | ⛔ Not currently supported | Listed because it is repeatedly proposed, and repeatedly declined: prediction markets are a regulated-market use, excluded under the API Terms of Use and from profit-share pricing. Do not infer support from anything else on this page. <br>*Menu:* Contract × stake <br>*Data:* Public order books and settlement history |
| **Procurement** | ⚪ Research | Supplier, quantity and timing selection against demand forecast and working-capital constraints — the buy side of the wholesale problem, inside an enterprise. <br>*Menu:* Line item × supplier × quantity × delivery window <br>*Data:* Quotation history, consumption records, supplier performance |
| **Healthcare insurance plan payments** | ⚪ Research | Payment and plan-assignment decisions scored on realized cost rather than on rules written a year ago. <br>*Menu:* Claim/plan × payment decision <br>*Data:* Claims tape, plan cost history |
| **Customs timing and clearance insurance** | ⚪ Research | Underwriting delay risk on shipments: enumerable consignments, measurable outcome, sharply biased history of what was previously covered. <br>*Menu:* Consignment × cover × premium <br>*Data:* Clearance timing records, route and broker history |
| **Fraud insurance** | ⚪ Research | Cover / decline and pricing on transaction fraud exposure, where refusal is most of the value. <br>*Menu:* Merchant/transaction class × cover × premium <br>*Data:* Chargeback and fraud-loss tape |

## Tier 1 — cleanest telemetry, minimal handling

The purest computable structure available to an individual operator: public comparable-sales data, enumerable listings, small units, fast settlement. The best place to start if you are claiming your first market.

| Market | State | Notes |
| --- | --- | --- |
| **Expiring domain drops** | ⚪ Research | The purest example on this list: about $10 units, 500-name portfolios, instant settlement, zero shipping. <br>*Menu:* Dropping name × bid <br>*Data:* GoDaddy / Dynadot auction and sales history |
| **Vinyl records** | ⚪ Research | Arguably the finest public comparable-sales dataset in any collectibles market. <br>*Menu:* Pressing × condition × price <br>*Data:* Discogs sales history |
| **Retro games and consoles** | ⚪ Research | Clean per-SKU time series with condition tiers already standardised by the market. <br>*Menu:* Title × condition tier × quantity <br>*Data:* PriceCharting time series |
| **Musical instruments and pedals** | ⚪ Research | High spread, strong seasonality, and unusually forgiving buyers. <br>*Menu:* Model × condition × price <br>*Data:* Reverb price guide, completed sales |
| **Retired LEGO sets** | ⚪ Research | The appreciation curve after set retirement is remarkably modelable. <br>*Menu:* Set × sealed/used × quantity <br>*Data:* BrickLink price guide and sales |
| **Trading cards — sport and TCG** | ⚪ Research | Grading arbitrage sits on top as a second, separate edge. <br>*Menu:* Card × grade × quantity <br>*Data:* TCGplayer, eBay sold, PSA population reports |
| **Sealed TCG product** | ⚪ Research | Sealed appreciation follows print-run and rotation mechanics rather than taste — mechanical, therefore learnable. <br>*Menu:* Product × sealed lot size <br>*Data:* Print-run and rotation schedules, sold comps |
| **Sneakers** | ⚪ Research | Margins are thin now, but the telemetry is institutional-grade. <br>*Menu:* Style × size × quantity <br>*Data:* StockX / GOAT bid-ask and sales history |
| **Amazon retail and online arbitrage** | 🟠 Pilot-ready | The existing wholesale pipeline pointed at a $500 buyer instead of a $500k one. <br>*Menu:* Listing × quantity <br>*Data:* Keepa price and rank history, fee schedules |
| **Textbooks** | ⚪ Research | Brutal, predictable seasonality. Abstention discipline matters more here than anywhere else in Tier 1. <br>*Menu:* ISBN × edition × quantity <br>*Data:* Sold comps, semester calendars, edition-change notices |

## Tier 2 — strong fit, needs handling or local presence

Same menu structure, but the operator touches physical goods, estimates repair cost, or has to be somewhere. Spreads are wider because of it.

| Market | State | Notes |
| --- | --- | --- |
| **Power tools** | ⚪ Research | Enormous spread on local marketplaces, near-instant liquidity. <br>*Data:* Marketplace sold listings |
| **Camera bodies and vintage lenses** | ⚪ Research | Deep, well-catalogued comparable history and a stable collector base. <br>*Data:* KEH, eBay sold |
| **Entry-tier watches and microbrands** | ⚪ Research | Reference-level comps; the risk is authentication, not pricing. <br>*Data:* Chrono24 comps |
| **Bicycles and e-bikes** | ⚪ Research | Sharply seasonal with high local spread — a timing problem as much as a selection one. <br>*Data:* Local marketplace sold listings |
| **Auto parts, OEM take-offs and cores** | ⚪ Research | Core charges create a price floor, which bounds the downside. <br>*Data:* Parts catalogues, core-charge schedules, sold comps |
| **Rare and out-of-print books** | ⚪ Research | Very long tail and very cheap entry — a good place to learn refusal. <br>*Data:* AbeBooks, Amazon sold history |
| **Model trains, die-cast and scale models** | ⚪ Research | An ageing collector base is itself a modelable signal. <br>*Data:* Auction records, collector marketplace comps |
| **Appliance and electronics repair-and-flip** | ⚪ Research | The repair-cost estimate is the hard variable; everything else is well observed. <br>*Data:* Sold comps, parts pricing, repair-time records |
| **Discontinued cosmetics and fragrance** | ⚪ Research | Discontinuation announcements are a clean event trigger. <br>*Data:* Discontinuation notices, sold comps |
| **Deadstock and branded apparel lots** | ⚪ Research | Lot-level pricing against per-unit resale telemetry. <br>*Data:* Wholesale lot offers, resale sold comps |
| **Liquidation and B-stock pallets** | ⚪ Research | Lumpy outcomes; manifest quality is the whole game. <br>*Data:* Pallet manifests, historical recovery rates |
| **Storage unit auctions** | ⚪ Research | High variance and thin telemetry, but fully enumerable and genuinely menu-shaped. <br>*Data:* Auction listings, realized resale outcomes |
| **Small regional estate auctions** | ⚪ Research | Badly catalogued — which is exactly where the mispricing lives. <br>*Data:* Auction catalogues, hammer prices |
| **Bin-store and thrift sourcing** | ⚪ Research | Per-item scanning: thousands of tiny decisions an hour, which is a volume the model is built for. <br>*Data:* Scanner lookups, sold comps |
| **Salvage vehicles** | ⚪ Research | Larger tickets with excellent public telemetry and repair-cost history. <br>*Data:* Copart / IAAI auction results |
| **Scrap metal and e-waste recovery** | ⚪ Research | Composition modelling from photographs against commodity prices. <br>*Data:* Commodity price feeds, recovery yields |
| **Rare plants and seeds** | ⚪ Research | The aroid boom showed how quickly telemetry-driven pricing forms in a new collectibles market. <br>*Data:* Marketplace sold history, auction results |
| **Small livestock and equipment auctions** | ⚪ Research | Deeply under-served by software, with regular, enumerable sale events. <br>*Data:* Sale-barn and auction records |

## Tier 3 — digital and intangible

No shipping, no storage. The telemetry is install counts, download history, traffic and expiry schedules. Fraud checking is the operator's main defence.

| Market | State | Notes |
| --- | --- | --- |
| **Micro-website and newsletter acquisitions** | ⚪ Research | Sub-$5k tier: enough listings per month to be a menu, not a one-off deal. <br>*Data:* Flippa, Acquire.com listing and sale history |
| **Chrome extensions, WordPress plugins, Shopify apps** | ⚪ Research | Install counts are the telemetry, and they are public. <br>*Data:* Store install counts, review velocity |
| **Print-on-demand design portfolios** | ⚪ Research | Hundreds of tiny bets with marketplace search volume as the demand signal. <br>*Data:* Marketplace search volume, sales history |
| **Stock asset portfolios — photo, audio, 3D** | ⚪ Research | Download history is public on most platforms, which makes revenue projectable. <br>*Data:* Platform download and revenue history |
| **Kindle and audiobook backlist rights** | ⚪ Research | Long-tail royalties against an acquisition price — a clean discounted-cash-flow menu. <br>*Data:* Sales rank history, royalty statements |
| **Faceless YouTube and TikTok channel acquisition** | ⚪ Research | High fraud rate — verify hard. Inflated metrics are the dominant failure mode, not mispricing. <br>*Data:* Public analytics, revenue verification |
| **Gift card arbitrage** | ⚪ Research | Thin, but genuinely computable and instantly settled. <br>*Data:* Raise / CardCash spreads and fill history |
| **Airline miles and points** | ⚪ Research | Devaluation risk is the modelable variable, and it is unusually well documented. <br>*Data:* Award charts, devaluation history |

## Tier 4 — operational and local

Recurring rather than one-shot: placement, utilization and routing decisions where the menu is rebuilt every period. Under-served by software, which is the opportunity.

| Market | State | Notes |
| --- | --- | --- |
| **Vending and ATM route placement** | ⚪ Research | Location selection is a textbook menu problem, and foot-traffic data is purchasable. <br>*Data:* Foot-traffic data, per-site takings history |
| **Equipment rental — tools, party, camera** | ⚪ Research | Utilization telemetry, recurring rather than one-shot: the menu rebuilds every period. <br>*Data:* Utilization and booking history, replacement costs |
| **Local lead arbitrage** | ⚪ Research | Buy leads, resell to contractors. Menu, budget constraint, savagely biased history — an excellent fit, and nobody models it. <br>*Data:* Lead cost, contact and conversion outcomes |
| **Peer storage and parking leasing** | ⚪ Research | Pricing and acceptance decisions per slot per period. <br>*Data:* Occupancy and rate history |
| **Small-space advertising** | ⚪ Research | Windows, boards and community screens: enumerable inventory, measurable response. <br>*Data:* Placement inventory, response rates |
| **Freelance-platform work arbitrage** | ⚪ Research | Structured sub-tasks on freelance marketplaces have the properties of a computable market: an enumerable menu of jobs, a bid, and a realized margin per job. <br>*Menu:* Job posting × bid × delivery slot <br>*Data:* Platform job feeds, historical bid/win and delivery cost |
| **Local services work arbitrage** | ⚪ Research | Appliance repair, A/C installation and similar trades: accept, price and schedule jobs against crew capacity. <br>*Menu:* Job × price × scheduled slot <br>*Data:* Job history, crew cost and utilization |
| **Equipment and vehicle/vessel rental flipping** | ⚪ Research | Buy the asset, rent it through its useful window, sell it at the right point — utilization and exit price decided jointly. <br>*Menu:* Asset × purchase price × rental period × exit date <br>*Data:* Rental rates and utilization, resale comps |

## Flagged — do not operate without counsel

These have textbook menu structure, which is exactly why they are listed. They also carry legal, regulatory or platform-rule exposure. HyperC declines them under the API Terms; they are documented so nobody rediscovers them the expensive way.

| Market | State | Notes |
| --- | --- | --- |
| **Tax lien certificates** | ⛔ Not currently supported | Perfect menu structure — and state-regulated, with long resolution horizons. Counsel first. |
| **Judgment and receivables purchasing** | ⛔ Not currently supported | Collections law applies to the operator, not only to the seller. |
| **Event tickets** | ⛔ Not currently supported | Resale is restricted or criminal depending on state and venue. Declined by policy. |
| **Reservation arbitrage** | ⛔ Not currently supported | Outright banned in several cities. Declined by policy. |
| **Aged social accounts** | ⛔ Not currently supported | Terms-of-service violation with account-death risk on both sides of the trade. |
| **Trademark and brand-name speculation** | ⛔ Not currently supported | UDRP proceedings will eat the portfolio. Distinct from ordinary expiring-domain drops. |

## Proposing a market

Members and enterprises propose markets continuously, and the catalogue is expected to
grow — several entries here started as a member's experiment. If you operate a market
that clears the four criteria, tell us: [hyperc.com/contact.html?topic=market](https://hyperc.com/contact.html?topic=market).

Supported-market workflows, weekly market drops and the skills that go with them are part
of the [P34 Membership](https://hyperc.com/membership.html).

*Catalogue version 2026-08-19. Regenerated from a single source; the website, this file and
`markets.json` are always in sync.*
