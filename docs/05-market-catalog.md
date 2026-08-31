# Computable markets — the catalogue

**Read this before the industry cases.** This is the overview of every market HyperC
has identified as computable or as a candidate for computability; the
[industry cases](https://hyperc.com/cases.html) and the
[enterprise page](https://hyperc.com/enterprise.html) are the deep dives that follow it.

A market is **computable** when feasible actions can be enumerated as a menu, outcomes can
be attributed back to decisions, constraints can be encoded, and repeated feedback exists.
One further condition carries most of the weight, and gives this class its other names —
**rejected-deals markets**, **partially observed markets**: outcomes must be *partially*
observed. Some can be replayed or simulated safely; others are genuinely enterable but were
never tested by the business, by the market, or by a trustworthy replay. On a market where
an ordinary trade would reveal everything, that split can be engineered — see [observed and
unobserved outcomes](01-overview.md#observed-and-unobserved-outcomes-the-load-bearing-requirement).
If your market clears that bar, P34 can be pointed at it — run the
[market-fit check](https://hyperc.com/markets.html) first.

> **Listing is evidence, not endorsement.** Every entry carries a state. Most of this
> catalogue is `⚪ Market blueprint`: the structure fits and members are welcome to
> experiment, but no maintained workflow ships yet. Do not read a listing as a claim that
> P34 ships that market today.

| State | Meaning |
| --- | --- |
| ✅ **Reference deployment** | Operated in production for members today — a maintained workflow HyperC currently services. |
| 🟠 **Active experiment** | Validated in live tests or in active enterprise discovery; deployed under review. |
| ⚪ **Market blueprint** | Mapped into a possible agent-operated business loop. Structure fits; member experiments welcome. |
| ⛔ **Separate perimeter** | Declined by policy or held in a separate regulatory perimeter. |

**135 markets catalogued** · 1 reference deployment · 6 active experiments · 115 market blueprints · 13 in a separate perimeter.

Machine-readable copy for agents: **[hyperc.com/markets.json](https://hyperc.com/markets.json)**
(same catalogue, same ids, same states) and **[hyperc.com/llms.txt](https://hyperc.com/llms.txt)**.

## Which market should you choose?

**Not necessarily the reference deployment.** Choose the market you already operate in, or one you know well. The state on each entry records where P34 has already been pointed — evidence, not a ranking and not a recommendation. The most developed market, Amazon wholesale, is also one of the hardest to enter: Amazon account management and wholesale supplier relationships are demanding operating problems that sit outside the model, and P34 does not solve them. What makes P34 work on a market is your data, your constraints and your operating knowledge, so a market you already understand beats a market with a pre-built workflow. Do not prioritise a market because we started there.

Practically: run the [market-fit check](https://hyperc.com/markets.html#fit) against the
market you already operate in or know well. If it clears the four criteria, that is your
market — bring its telemetry and constraints. Use the reference deployment and the active
experiments as evidence that the method works, not as a shortlist to pick from. Where a market carries a
**Hard to operate** note below, that difficulty is real and is not something P34 removes.

## Core markets

Institutional scale — the markets HyperC and its enterprise partners work directly. Large tickets, deep telemetry, and in several cases a live deployment behind them.

| Market | State | Notes |
| --- | --- | --- |
| **Amazon wholesale — US & EU** | ✅ Reference deployment | The founding deployment: purchase and shipping portfolio decisions from live wholesale menus, in production since 2023 at roughly $100M/yr reseller scale (company-reported). <br>⚠️ *Hard to operate:* The best-understood market here and one of the hardest to operate — and the hard parts are not the model. Amazon account management (ungating, brand and IP complaints, performance metrics, suspension and reinstatement) and wholesale supplier relationships (winning authorised distributor accounts at all, minimums, credit terms) are demanding operating problems that P34 does not solve. Enter it because you already run it, not because it is the developed one. <br>*Menu:* SKU × quantity × supplier offer, with lead times and fees <br>*Data:* Supplier price lists, catalogue and fee data, sales velocity, returns |
| **Micro-lending — individual** | 🟠 Active experiment | Lend / no-lend calls where credit history is sparse or absent. About 3,000 loans issued in a live model test (2025). Regulated commerce: gated behind market-specific compliance review. <br>*Menu:* Applicant × offered principal × term <br>*Data:* Application attributes, repayment tape, collections outcomes |
| **Crypto transaction routing** | ⚪ Market blueprint | Routing and execution across venues in adversarial order flow. Deployed in research; a separate product and regulatory perimeter, not part of membership. <br>*Menu:* Route × size × venue, per transfer <br>*Data:* Venue depth, spread and fee telemetry, settlement latency |
| **Constrained FX invoice payments** | ⚪ Market blueprint | Which invoices to settle, in which currency and when, under liquidity and corridor constraints — a scheduling problem with a measurable cost of being wrong. <br>*Menu:* Invoice × corridor × settlement date <br>*Data:* Corridor rates and fees, liquidity positions, invoice ageing |
| **Casino customer incentivisation** | ⚪ Market blueprint | Offer selection and sizing scored on lifetime player economics rather than redemption rate, with abstention when the economics do not clear the bar. <br>*Menu:* Player segment × offer × value <br>*Data:* Play history, redemption and margin tape |
| **Prop trading risk management** | ⚪ Market blueprint | Allocation and limit decisions across traders and strategies. Financial perimeter: excluded from profit-share pricing and gated under the API Terms. <br>*Menu:* Trader/strategy × capital allocation × limit <br>*Data:* Realized P&L tape, drawdown and exposure history |
| **Manager underwriting — CLO / private credit** | 🟠 Active experiment | Manager selection as a menu decision under partial observability: candidate managers, sparse comparable histories, a measurable recovery target. Enterprise discovery case. <br>*Menu:* Candidate manager × commitment size <br>*Data:* Historical manager performance, recovery and default records |
| **Card overdraft and micro-loan offers** | 🟠 Active experiment | Limit increases, overdraft and micro-loan offers treated as one portfolio decision scored on expected lifetime economics. Designed for shadow evaluation against the incumbent policy first. <br>*Menu:* Cardholder × offer type × limit <br>*Data:* Balance and utilisation history, loss tape, incumbent policy decisions |
| **Bank customer onboarding** | 🟠 Active experiment | Onboarding incentives selected and sized on lifetime economics rather than conversion alone — refusing the offers that will not pay for themselves. <br>*Menu:* Prospect segment × incentive × value <br>*Data:* Onboarding cohorts, product uptake, lifetime margin |
| **Amazon discounter / online arbitrage at scale** | 🟠 Active experiment | Retail and online arbitrage run as a portfolio on public telemetry, pointed at small-ticket buyers rather than wholesale lots. <br>*Menu:* Discounted listing × quantity <br>*Data:* Keepa-class price and rank history, fee and returns data |
| **Alt-coin hedge fund** | ⛔ Separate perimeter | Structurally a menu problem, but a financial-market perimeter. Excluded from membership and from profit-share pricing. <br>*Menu:* Asset × position size × horizon <br>*Data:* Venue price history, liquidity and flow telemetry |
| **Exotic asset hedge fund** | ⛔ Separate perimeter | Illiquid and non-standard asset selection. Same perimeter and same exclusion as the above. <br>*Menu:* Asset × allocation <br>*Data:* Sparse comparable sales, holding-cost and carry data |
| **MCA — merchant cash advance (B2B)** | ⚪ Market blueprint | Advance / decline and sizing against future receivables, where the historical book is severely selection-biased — the failure mode P34 is built for. <br>*Menu:* Merchant × advance amount × factor rate <br>*Data:* Processing volume history, repayment and default tape |
| **Partial payment acceptance (bank)** | ⚪ Market blueprint | Which partial settlements to accept on delinquent balances, and at what discount — a recovery-maximisation menu, not a collections script. <br>*Menu:* Account × settlement offer × discount <br>*Data:* Delinquency ageing, historical recovery outcomes |
| **Prediction markets** | ⛔ Separate perimeter | Listed because it is repeatedly proposed, and repeatedly declined: prediction markets are a regulated-market use, excluded under the API Terms of Use and from profit-share pricing. Do not infer support from anything else on this page. <br>*Menu:* Contract × stake <br>*Data:* Public order books and settlement history |
| **Procurement** | ⚪ Market blueprint | Supplier, quantity and timing selection against demand forecast and working-capital constraints — the buy side of the wholesale problem, inside an enterprise. <br>*Menu:* Line item × supplier × quantity × delivery window <br>*Data:* Quotation history, consumption records, supplier performance |
| **Healthcare insurance plan payments** | ⚪ Market blueprint | Payment and plan-assignment decisions scored on realized cost rather than on rules written a year ago. <br>*Menu:* Claim/plan × payment decision <br>*Data:* Claims tape, plan cost history |
| **Customs timing and clearance insurance** | ⚪ Market blueprint | Underwriting delay risk on shipments: enumerable consignments, measurable outcome, sharply biased history of what was previously covered. <br>*Menu:* Consignment × cover × premium <br>*Data:* Clearance timing records, route and broker history |
| **Fraud insurance** | ⚪ Market blueprint | Cover / decline and pricing on transaction fraud exposure, where refusal is most of the value. <br>*Menu:* Merchant/transaction class × cover × premium <br>*Data:* Chargeback and fraud-loss tape |
| **SMB working-capital lending** | ⚪ Market blueprint | Businesses conventional underwriting declines because the file is thin or the shape is unfamiliar, not because the economics fail. Regulated commerce: gated behind market-specific compliance review. <br>*Menu:* Business × principal × term × price <br>*Data:* Bank-transaction and accounting feeds, repayment tape, incumbent decline reasons |
| **Invoice factoring** | ⚪ Market blueprint | Invoices and firms left unfinanced because diligence per invoice costs more than the spread. The rejected set is observable where a factor logs what it turned down. <br>*Menu:* Invoice × advance rate × fee × term <br>*Data:* Invoice and ageing tape, debtor payment history, dilution and dispute records |
| **Purchase-order financing** | ⚪ Market blueprint | POs declined because underwriting the buyer, the supplier and the shipment at once is expensive relative to ticket size. <br>*Menu:* PO × funded share × fee × expected settlement <br>*Data:* Buyer credit history, supplier delivery record, shipment and settlement timings |
| **Small-ticket equipment financing** | ⚪ Market blueprint | Transactions beneath a lender's attention threshold, where the asset is recoverable but the file is too small to justify manual review. <br>*Menu:* Applicant × asset × advance × term <br>*Data:* Asset resale comparables, obligor history, recovery and repossession outcomes |
| **Auto lending** | ⚪ Market blueprint | Applicant-vehicle-downpayment-term combinations declined by scorecards built on approved-applicant data only. Regulated: fair-lending review is a precondition, not a formality. <br>⚠️ *Hard to operate:* Consumer credit. Adverse-action, fair-lending and disparate-impact obligations attach to every decline, including the ones a model makes. This is a compliance project with a model inside it. <br>*Menu:* Applicant × vehicle × advance × term × rate <br>*Data:* Application and decline records, vehicle valuation series, repayment and recovery tape |
| **Trade credit and payment terms** | ⚪ Market blueprint | Customer, limit and payment-term combinations suppliers refuse — a decision usually made by policy table rather than by expected economics. <br>*Menu:* Customer × credit limit × payment term <br>*Data:* Order and payment history, ageing, write-off tape |
| **Freight invoice financing** | ⚪ Market blueprint | Carrier invoices skipped because verification against the load and the broker costs more than the fee on a small haul. <br>*Menu:* Carrier × invoice × advance × expected payment date <br>*Data:* Load and rate confirmations, broker payment history, settlement timings |
| **Specialty commercial insurance** | ⚪ Market blueprint | Small unusual risks declined or priced defensively because they do not fit a rating table. Regulated: rate filing and licensing sit outside the model. <br>⚠️ *Hard to operate:* Insurance is licensed, filed and supervised per jurisdiction. A pricing model is not a rate filing, and binding authority is not something P34 confers. <br>*Menu:* Risk × coverage × limit × premium <br>*Data:* Submission and decline records, loss runs, exposure characteristics |

## Tier 1 — cleanest telemetry, minimal handling

The purest computable structure available to an individual operator: public comparable-sales data, enumerable listings, small units, fast settlement. The best place to start if you are claiming your first market.

| Market | State | Notes |
| --- | --- | --- |
| **Expiring domain drops** | ⚪ Market blueprint | The purest example on this list: about $10 units, 500-name portfolios, instant settlement, zero shipping. <br>*Menu:* Dropping name × bid <br>*Data:* GoDaddy / Dynadot auction and sales history |
| **Vinyl records** | ⚪ Market blueprint | Arguably the finest public comparable-sales dataset in any collectibles market. <br>*Menu:* Pressing × condition × price <br>*Data:* Discogs sales history |
| **Retro games and consoles** | ⚪ Market blueprint | Clean per-SKU time series with condition tiers already standardised by the market. <br>*Menu:* Title × condition tier × quantity <br>*Data:* PriceCharting time series |
| **Musical instruments and pedals** | ⚪ Market blueprint | High spread, strong seasonality, and unusually forgiving buyers. <br>*Menu:* Model × condition × price <br>*Data:* Reverb price guide, completed sales |
| **Retired LEGO sets** | ⚪ Market blueprint | The appreciation curve after set retirement is remarkably modelable. <br>*Menu:* Set × sealed/used × quantity <br>*Data:* BrickLink price guide and sales |
| **Trading cards — sport and TCG** | ⚪ Market blueprint | Grading arbitrage sits on top as a second, separate edge. <br>*Menu:* Card × grade × quantity <br>*Data:* TCGplayer, eBay sold, PSA population reports |
| **Sealed TCG product** | ⚪ Market blueprint | Sealed appreciation follows print-run and rotation mechanics rather than taste — mechanical, therefore learnable. <br>*Menu:* Product × sealed lot size <br>*Data:* Print-run and rotation schedules, sold comps |
| **Sneakers** | ⚪ Market blueprint | Margins are thin now, but the telemetry is institutional-grade. <br>*Menu:* Style × size × quantity <br>*Data:* StockX / GOAT bid-ask and sales history |
| **Amazon retail and online arbitrage** | 🟠 Active experiment | The existing wholesale pipeline pointed at a $500 buyer instead of a $500k one. <br>*Menu:* Listing × quantity <br>*Data:* Keepa price and rank history, fee schedules |
| **Textbooks** | ⚪ Market blueprint | Brutal, predictable seasonality. Abstention discipline matters more here than anywhere else in Tier 1. <br>*Menu:* ISBN × edition × quantity <br>*Data:* Sold comps, semester calendars, edition-change notices |

## Tier 2 — strong fit, needs handling or local presence

Same menu structure, but the operator touches physical goods, estimates repair cost, or has to be somewhere. Spreads are wider because of it.

| Market | State | Notes |
| --- | --- | --- |
| **Power tools** | ⚪ Market blueprint | Enormous spread on local marketplaces, near-instant liquidity. <br>*Data:* Marketplace sold listings |
| **Camera bodies and vintage lenses** | ⚪ Market blueprint | Deep, well-catalogued comparable history and a stable collector base. <br>*Data:* KEH, eBay sold |
| **Entry-tier watches and microbrands** | ⚪ Market blueprint | Reference-level comps; the risk is authentication, not pricing. <br>*Data:* Chrono24 comps |
| **Bicycles and e-bikes** | ⚪ Market blueprint | Sharply seasonal with high local spread — a timing problem as much as a selection one. <br>*Data:* Local marketplace sold listings |
| **Auto parts, OEM take-offs and cores** | ⚪ Market blueprint | Core charges create a price floor, which bounds the downside. <br>*Data:* Parts catalogues, core-charge schedules, sold comps |
| **Rare and out-of-print books** | ⚪ Market blueprint | Very long tail and very cheap entry — a good place to learn refusal. <br>*Data:* AbeBooks, Amazon sold history |
| **Model trains, die-cast and scale models** | ⚪ Market blueprint | An ageing collector base is itself a modelable signal. <br>*Data:* Auction records, collector marketplace comps |
| **Appliance and electronics repair-and-flip** | ⚪ Market blueprint | The repair-cost estimate is the hard variable; everything else is well observed. <br>*Data:* Sold comps, parts pricing, repair-time records |
| **Discontinued cosmetics and fragrance** | ⚪ Market blueprint | Discontinuation announcements are a clean event trigger. <br>*Data:* Discontinuation notices, sold comps |
| **Deadstock and branded apparel lots** | ⚪ Market blueprint | Lot-level pricing against per-unit resale telemetry. <br>*Data:* Wholesale lot offers, resale sold comps |
| **Liquidation and B-stock pallets** | ⚪ Market blueprint | Lumpy outcomes; manifest quality is the whole game. <br>*Data:* Pallet manifests, historical recovery rates |
| **Storage unit auctions** | ⚪ Market blueprint | High variance and thin telemetry, but fully enumerable and genuinely menu-shaped. <br>*Data:* Auction listings, realized resale outcomes |
| **Small regional estate auctions** | ⚪ Market blueprint | Badly catalogued — which is exactly where the mispricing lives. <br>*Data:* Auction catalogues, hammer prices |
| **Bin-store and thrift sourcing** | ⚪ Market blueprint | Per-item scanning: thousands of tiny decisions an hour, which is a volume the model is built for. <br>*Data:* Scanner lookups, sold comps |
| **Salvage vehicles** | ⚪ Market blueprint | Larger tickets with excellent public telemetry and repair-cost history. <br>*Data:* Copart / IAAI auction results |
| **Scrap metal and e-waste recovery** | ⚪ Market blueprint | Composition modelling from photographs against commodity prices. <br>*Data:* Commodity price feeds, recovery yields |
| **Rare plants and seeds** | ⚪ Market blueprint | The aroid boom showed how quickly telemetry-driven pricing forms in a new collectibles market. <br>*Data:* Marketplace sold history, auction results |
| **Small livestock and equipment auctions** | ⚪ Market blueprint | Deeply under-served by software, with regular, enumerable sale events. <br>*Data:* Sale-barn and auction records |
| **Walmart and marketplace wholesale** | ⚪ Market blueprint | Supplier lots existing resellers pass on. Same menu shape as the Amazon deployment against a different fee, velocity and returns regime. <br>*Menu:* SKU × quantity × supplier offer × marketplace <br>*Data:* Supplier price lists, marketplace fee schedules, rank and velocity history |
| **Retail clearance inventory** | ⚪ Market blueprint | Store-level clearance other resellers ignore because it is scattered across locations and priced per store rather than per catalogue. <br>*Menu:* Store × SKU × price × quantity × exit channel <br>*Data:* Store-level clearance feeds, comparable sold prices, fee and shipping tables |
| **Distributor excess inventory** | ⚪ Market blueprint | Overstock lots rejected by normal distribution channels — the goods are fine, the channel is full. <br>*Menu:* Lot × price × quantity × onward channel <br>*Data:* Excess and overstock listings, comparable trade prices, carrying-cost assumptions |
| **Closeout merchandise** | ⚪ Market blueprint | Brand, SKU and quantity deals buyers decline because the margin looks too thin before fees, returns and sell-through are modelled properly. <br>*Menu:* Deal × quantity × price × expected sell-through <br>*Data:* Closeout offer sheets, comparable sold prices, returns and fee history |
| **Returned-goods resale** | ⚪ Market blueprint | Return lots rejected because condition and recoverable value are hard to estimate from a manifest. The estimation error is the market. <br>*Menu:* Lot × bid × grading assumption × exit channel <br>*Data:* Manifests, historical grade-out rates, per-condition sold comparables |
| **Refurbished electronics** | ⚪ Market blueprint | Devices declined at particular acquisition and repair-cost combinations — a joint estimate of parts, labour, failure rate and resale. <br>*Menu:* Device × acquisition price × repair spend × exit channel <br>*Data:* Parts and labour costs, repair success rates, per-condition sold comparables |
| **Spare-parts stocking** | ⚪ Market blueprint | Low-volume parts nobody stocks because expected demand is hard to estimate — a portfolio decision across thousands of slow-moving SKUs. <br>*Menu:* Part × stocking quantity × reorder point <br>*Data:* Historical consumption, lead times, obsolescence and equipment-install base |

## Tier 3 — digital and intangible

No shipping, no storage. The telemetry is install counts, download history, traffic and expiry schedules. Fraud checking is the operator's main defence.

| Market | State | Notes |
| --- | --- | --- |
| **Micro-website and newsletter acquisitions** | ⚪ Market blueprint | Sub-$5k tier: enough listings per month to be a menu, not a one-off deal. <br>*Data:* Flippa, Acquire.com listing and sale history |
| **Chrome extensions, WordPress plugins, Shopify apps** | ⚪ Market blueprint | Install counts are the telemetry, and they are public. <br>*Data:* Store install counts, review velocity |
| **Print-on-demand design portfolios** | ⚪ Market blueprint | Hundreds of tiny bets with marketplace search volume as the demand signal. <br>*Data:* Marketplace search volume, sales history |
| **Stock asset portfolios — photo, audio, 3D** | ⚪ Market blueprint | Download history is public on most platforms, which makes revenue projectable. <br>*Data:* Platform download and revenue history |
| **Kindle and audiobook backlist rights** | ⚪ Market blueprint | Long-tail royalties against an acquisition price — a clean discounted-cash-flow menu. <br>*Data:* Sales rank history, royalty statements |
| **Faceless YouTube and TikTok channel acquisition** | ⚪ Market blueprint | High fraud rate — verify hard. Inflated metrics are the dominant failure mode, not mispricing. <br>*Data:* Public analytics, revenue verification |
| **Gift card arbitrage** | ⚪ Market blueprint | Thin, but genuinely computable and instantly settled. <br>*Data:* Raise / CardCash spreads and fill history |
| **Airline miles and points** | ⚪ Market blueprint | Devaluation risk is the modelable variable, and it is unusually well documented. <br>*Data:* Award charts, devaluation history |

## Tier 4 — operational and local

Recurring rather than one-shot: placement, utilization and routing decisions where the menu is rebuilt every period. Under-served by software, which is the opportunity.

| Market | State | Notes |
| --- | --- | --- |
| **Vending and ATM route placement** | ⚪ Market blueprint | Location selection is a textbook menu problem, and foot-traffic data is purchasable. <br>*Data:* Foot-traffic data, per-site takings history |
| **Equipment rental — tools, party, camera** | ⚪ Market blueprint | Utilization telemetry, recurring rather than one-shot: the menu rebuilds every period. <br>*Data:* Utilization and booking history, replacement costs |
| **Local lead arbitrage** | ⚪ Market blueprint | Buy leads, resell to contractors. Menu, budget constraint, savagely biased history — an excellent fit, and nobody models it. <br>*Data:* Lead cost, contact and conversion outcomes |
| **Peer storage and parking leasing** | ⚪ Market blueprint | Pricing and acceptance decisions per slot per period. <br>*Data:* Occupancy and rate history |
| **Small-space advertising** | ⚪ Market blueprint | Windows, boards and community screens: enumerable inventory, measurable response. <br>*Data:* Placement inventory, response rates |
| **Freelance-platform work arbitrage** | ⚪ Market blueprint | Structured sub-tasks on freelance marketplaces have the properties of a computable market: an enumerable menu of jobs, a bid, and a realized margin per job. <br>*Menu:* Job posting × bid × delivery slot <br>*Data:* Platform job feeds, historical bid/win and delivery cost |
| **Local services work arbitrage** | ⚪ Market blueprint | Appliance repair, A/C installation and similar trades: accept, price and schedule jobs against crew capacity. <br>*Menu:* Job × price × scheduled slot <br>*Data:* Job history, crew cost and utilization |
| **Equipment and vehicle/vessel rental flipping** | ⚪ Market blueprint | Buy the asset, rent it through its useful window, sell it at the right point — utilization and exit price decided jointly. <br>*Menu:* Asset × purchase price × rental period × exit date <br>*Data:* Rental rates and utilization, resale comps |

## Demand and customer acquisition

The menu is a cell in a grid — audience × creative × offer × time × placement × bid — and a human instantiates a minute fraction of it. Everything never tested is the reject set, and the outcome is measurable per cell.

| Market | State | Notes |
| --- | --- | --- |
| **Paid-search keyword bidding** | ⚪ Market blueprint | Keyword, bid, geography and time combinations campaigns never buy. The menu is enumerable and the outcome per cell is measurable, which is the whole requirement. <br>*Menu:* Keyword × match type × geo × time × bid <br>*Data:* Search-term and auction reports, conversion and margin tape, incumbent bid policy |
| **Social audience cohorts** | ⚪ Market blueprint | Audience combinations excluded from existing campaigns — usually by habit or by a rule written once, not by measured economics. <br>*Menu:* Audience × creative × placement × budget <br>*Data:* Delivery and conversion reports, cohort margin, historical exclusions |
| **Display and programmatic inventory** | ⚪ Market blueprint | Impressions declined below a bid threshold. Attribution is the hard part and it is the reason the reject set stays large. <br>⚠️ *Hard to operate:* Attribution on display is contested and view-through effects are easy to overstate. Without a clean incrementality design the measured outcome can be an artefact of the measurement. <br>*Menu:* Placement × audience × time × bid <br>*Data:* Bid-stream and win/loss logs, post-click and incrementality tests, margin tape |
| **Retargeting cohorts** | ⚪ Market blueprint | Users not retargeted because simple recency-and-frequency rules rank them poorly, though their expected economics may clear. <br>*Menu:* Cohort × window × frequency cap × bid <br>*Data:* Session and cart telemetry, conversion lags, contribution margin per cohort |
| **Affiliate and publisher traffic** | ⚪ Market blueprint | Publishers and traffic sources merchants decline wholesale, where the honest answer varies by source rather than by category. <br>⚠️ *Hard to operate:* Affiliate fraud and incentivised traffic are endemic; a source that looks profitable on last-click can be buying credit for demand you already had. <br>*Menu:* Publisher × offer × commission × cap <br>*Data:* Per-source conversion and refund rates, chargeback and fraud history |
| **Lead purchasing** | ⚪ Market blueprint | Leads buyers refuse at a given price. Distinct from generating leads (see local lead arbitrage): here the menu is priced inventory someone else produced. <br>*Menu:* Lead source × attribute set × price × volume cap <br>*Data:* Contact-to-close rates by attribute, revenue per closed lead, refund and dispute records |
| **B2B outbound prospecting** | ⚪ Market blueprint | Accounts a sales team never works because human capacity, not expected value, sets the list length. <br>*Menu:* Account × contact × sequence × timing <br>*Data:* Firmographic and intent signals, historical win rates by segment, deal margin |
| **Lifecycle email and messaging** | ⚪ Market blueprint | Customer, message and timing combinations never tested — a grid with millions of cells and a few dozen instantiated. <br>*Menu:* Segment × message × send time × frequency <br>*Data:* Send, open and conversion logs, unsubscribe cost, per-cohort margin |
| **Coupon and promotion targeting** | ⚪ Market blueprint | Discounts not offered to particular cohorts — and, just as often, discounts given to cohorts that would have bought anyway. Refusal is the valuable half. <br>*Menu:* Cohort × discount depth × channel × window <br>*Data:* Redemption and holdout results, baseline purchase rates, margin per order |
| **Marketplace sponsored listings** | ⚪ Market blueprint | Product, keyword and position bids sellers never place, on inventory whose own margin they already know exactly. <br>*Menu:* Product × keyword × position × bid <br>*Data:* Advertising reports, organic-rank series, unit economics per SKU |

## Freight, mobility and physical capacity

Rolling menus of loads, lanes, slots and spaces. What one operator must decline — wrong direction, wrong date, too small — is exactly what fits another, so the reject set is operator-dependent rather than uniformly bad.

| Market | State | Notes |
| --- | --- | --- |
| **Truckload boards** | ⚪ Market blueprint | Loads carriers decline. The classic operator-dependent reject: a load that is wrong for one truck is right for the truck that needs that lane today. <br>*Menu:* Load × lane × pickup window × rate <br>*Data:* Board postings and rate history, deadhead distance, hours-of-service and fuel cost |
| **Partial-truckload consolidation** | ⚪ Market blueprint | Small shipment combinations nobody assembles because the search over compatible pairs is combinatorial and manual. <br>*Menu:* Shipment set × route × sequence × price <br>*Data:* Shipment dimensions and windows, lane rates, terminal and handling costs |
| **Backhaul matching** | ⚪ Market blueprint | Return-leg loads missed or declined — value that exists only because the truck is already going that way. <br>*Menu:* Return leg × candidate load × rate × delay tolerance <br>*Data:* Fleet position and schedule, historical lane rates, empty-mile cost |
| **Last-mile delivery jobs** | ⚪ Market blueprint | Routes and jobs that look unattractive under simple dispatch rules but clear once sequencing and drop density are priced properly. <br>*Menu:* Job set × route × time window × pay <br>*Data:* Historical route times, drop density, failed-delivery and return rates |
| **Courier and same-day capacity** | ⚪ Market blueprint | Time, location and delivery combinations left unassigned when demand and couriers are both moving. <br>*Menu:* Courier × job × time slot × price <br>*Data:* Job and completion logs, positioning history, cancellation rates |
| **Container repositioning** | ⚪ Market blueprint | Empty moves operators decline, where the cost of being in the wrong place later is the real quantity being traded. <br>*Menu:* Container × origin/destination × date × cost <br>*Data:* Equipment positions, imbalance forecasts, per-lane repositioning cost |
| **Air cargo capacity** | ⚪ Market blueprint | Small cargo blocks not accepted on particular flights because the handling overhead per block is human. <br>*Menu:* Flight × block size × rate × handling window <br>*Data:* Capacity and load-factor history, per-lane rate series, handling cost |
| **Ocean freight capacity** | ⚪ Market blueprint | Shipment, lane, date and rate combinations that go unbooked while equivalent capacity sails empty. <br>*Menu:* Shipment × lane × sailing date × rate <br>*Data:* Sailing schedules, historical spot and contract rates, rollover history |
| **Warehouse overflow space** | ⚪ Market blueprint | Short-term storage requests warehouses reject because the request does not fit the shape of a standard contract. <br>*Menu:* Site × pallet count × duration × rate <br>*Data:* Occupancy and turnover history, handling cost per pallet, seasonal demand series |
| **Parking and kerbside capacity pricing** | ⚪ Market blueprint | Space, time and price combinations conventional pricing leaves unused. Operator-side pricing rather than leasing out your own space. <br>*Menu:* Space class × time block × price <br>*Data:* Occupancy telemetry, event and demand calendars, enforcement and turnover data |

## Compute, energy and connectivity

Perishable capacity priced by time. A GPU-hour, a curtailment window or a bandwidth block that goes unsold is gone, which makes the decline decision continuous and the outcome cleanly attributable.

| Market | State | Notes |
| --- | --- | --- |
| **GPU spot capacity** | ⚪ Market blueprint | Workload, hardware, duration and price combinations that never get matched. Capacity is perishable and the outcome per job is measurable, which is a clean menu. <br>*Menu:* Workload × GPU class × duration × price × SLA <br>*Data:* Spot price series, job runtime and failure history, energy and interconnect cost |
| **Cloud reserved-capacity reuse** | ⚪ Market blueprint | Reservations owners do not reuse efficiently — committed spend that expires unconsumed while equivalent demand pays on-demand rates. <br>⚠️ *Hard to operate:* Provider terms govern whether commitments may be transferred or resold at all, and they differ per provider. Read them before modelling anything. <br>*Menu:* Commitment × workload × window × internal price <br>*Data:* Commitment inventory and expiry, utilisation history, on-demand price series |
| **Idle enterprise GPU capacity** | ⚪ Market blueprint | Small compute jobs that cannot justify a human sales conversation, against hardware already bought and idle. <br>*Menu:* Cluster window × job × price × priority <br>*Data:* Utilisation telemetry, job queue history, marginal power cost |
| **CPU batch workloads** | ⚪ Market blueprint | Low-priority jobs rejected by conventional scheduling, where deferral cost is small and capacity is cheap at the right hour. <br>*Menu:* Job × window × priority × price <br>*Data:* Queue and completion history, deadline sensitivity, time-of-day cost |
| **Data-centre power allocation** | ⚪ Market blueprint | Workloads declined at particular power and time combinations — a scheduling problem against a hard physical envelope. <br>*Menu:* Workload × power envelope × time block <br>*Data:* Power draw telemetry, tariff and demand-charge schedules, thermal headroom |
| **Demand-response curtailment** | ⚪ Market blueprint | Load-curtailment opportunities businesses leave unmonetised because the operational cost of curtailing is never quantified against the payment. <br>*Menu:* Site × load block × curtailment window × payment <br>*Data:* Interval meter data, programme price signals, production-loss cost |
| **Distributed battery dispatch** | ⚪ Market blueprint | Time, location and charge/discharge actions conventional rules skip, where degradation is a real cost that a naive optimiser ignores. <br>*Menu:* Asset × time block × charge/discharge × market <br>*Data:* Price series, state-of-charge and degradation curves, connection limits |
| **Rooftop solar surplus** | ⚪ Market blueprint | Local generation and time combinations poorly monetised under flat export tariffs. <br>*Menu:* Site × export block × price × storage decision <br>*Data:* Generation and consumption telemetry, tariff schedules, weather forecasts |
| **Wholesale bandwidth and transit** | ⚪ Market blueprint | Capacity, route and duration deals carriers do not assemble because the search across routes and terms is manual. <br>*Menu:* Route × capacity × term × price <br>*Data:* Route inventory and utilisation, historical transit pricing, latency and SLA records |
| **Failover and burst connectivity** | ⚪ Market blueprint | Temporary capacity that is never dynamically marketed, so it is held idle against an outage that mostly does not happen. <br>*Menu:* Site × capacity × standby window × price <br>*Data:* Link utilisation, outage history, contractual burst allowances |

## Industrial supply, surplus and production capacity

B2B goods and slots where matching is the hard part: surplus, by-products, off-spec lots and idle production time that conventional channels skip because valuation and counterparty search cost more than the ticket.

| Market | State | Notes |
| --- | --- | --- |
| **Dealer used-car auctions** | ⚪ Market blueprint | Vehicle and bid combinations dealers decline. Distinct from salvage: these run, and the estimate is reconditioning plus retail days-to-turn. <br>*Menu:* Vehicle × bid × reconditioning spend × exit channel <br>*Data:* Auction result history, condition reports, retail comparable prices and turn times |
| **Heavy equipment auctions** | ⚪ Market blueprint | Machines rejected because repair and resale economics are uncertain and inspection is expensive. <br>*Menu:* Machine × bid × repair spend × resale channel <br>*Data:* Auction comparables, hours and service records, parts and transport costs |
| **Industrial surplus equipment** | ⚪ Market blueprint | Factory equipment no conventional reseller wants to underwrite, where the buyer set is small, findable and specific. <br>*Menu:* Asset × price × removal cost × buyer segment <br>*Data:* Comparable sales, rigging and transport quotes, install-base and demand signals |
| **Construction material surplus** | ⚪ Market blueprint | Excess steel, lumber and fixtures ignored because matching a specific lot to a specific job is the expensive part. <br>*Menu:* Lot × spec × location × price <br>*Data:* Project and tender pipelines, commodity price series, haulage cost |
| **Agricultural surplus and off-grade lots** | ⚪ Market blueprint | Crop lots conventional channels skip on grade, size or location — perishable, seasonal, and priced by whoever shows up. <br>⚠️ *Hard to operate:* Perishability and food-safety rules are unforgiving: a modelling error here spoils rather than sits, and handling is licensed in most jurisdictions. <br>*Menu:* Lot × grade × location × price × exit window <br>*Data:* Grade and yield records, regional price series, storage and haulage cost |
| **Short-dated food closeouts** | ⚪ Market blueprint | Inventory rejected because remaining shelf life against sell-through rate is a calculation nobody does per lot. <br>⚠️ *Hard to operate:* Date-code, labelling and cold-chain rules govern what may be resold and where. Treat them as constraints, not as friction. <br>*Menu:* Lot × remaining shelf life × price × channel <br>*Data:* Sell-through rates by channel, date-code data, storage and disposal costs |
| **Industrial by-products and side streams** | ⚪ Market blueprint | Secondary outputs firms currently pay to dispose of. The interesting case: a search over combinations where negative-value disposal becomes positive-value supply for someone else. <br>⚠️ *Hard to operate:* Waste classification, transport and permitting law decides whether a stream is a product or a regulated waste — and getting that wrong is a serious matter, not a paperwork slip. <br>*Menu:* Stream × specification × counterparty × price <br>*Data:* Composition and volume records, disposal cost, buyer specifications and permits |
| **Spare manufacturing capacity** | ⚪ Market blueprint | Production slots factories do not monetise, where the marginal cost of a slot is known and the search for a fitting job is not. <br>*Menu:* Machine group × slot × job type × price <br>*Data:* Utilisation and changeover history, marginal cost per slot, quote win/loss records |
| **Small-batch and custom orders** | ⚪ Market blueprint | Custom jobs factories reject because quotation and setup overhead dominates the ticket — a human transaction cost, not a negative margin. <br>*Menu:* Enquiry × batch size × setup × quoted price <br>*Data:* Historical quotes and win rates, setup and run times, scrap and rework rates |

## Contract work, bids and recovery

Jobs declined for human transaction cost rather than negative value — reading the tender, estimating, scheduling, chasing. The reject frontier here moves when the cost of evaluating a job falls.

| Market | State | Notes |
| --- | --- | --- |
| **Home-service jobs** | ⚪ Market blueprint | Plumbing, electrical and HVAC jobs declined because the scheduling is awkward rather than because the job is unprofitable. <br>*Menu:* Job × technician × time slot × quoted price <br>*Data:* Job duration and callback history, travel times, per-job margin |
| **Commercial cleaning contracts** | ⚪ Market blueprint | Sites and bids operators never pursue, where the estimate is area, frequency, staffing and travel. <br>*Menu:* Site × scope × frequency × bid <br>*Data:* Historical bids and win rates, labour hours per site, retention history |
| **Landscaping and grounds contracts** | ⚪ Market blueprint | Small local contracts beneath the cost of a manual sales visit — a route-density problem as much as a pricing one. <br>*Menu:* Property × service plan × season × bid <br>*Data:* Route density and travel time, crew hours per property, renewal rates |
| **Moving jobs** | ⚪ Market blueprint | Origin, destination and date combinations movers reject, where the return leg and crew utilisation decide the answer. <br>*Menu:* Job × crew × date × route × price <br>*Data:* Historical job times, damage-claim rates, backhaul and utilisation data |
| **Field equipment repair** | ⚪ Market blueprint | Low-probability or geographically inconvenient jobs, priced without knowing whether the part will be in the van. <br>*Menu:* Call × technician × parts kit × price <br>*Data:* First-time-fix rates, parts consumption, travel and diagnostic times |
| **Medical billing recovery** | ⚪ Market blueprint | Underpaid and denied claims providers do not pursue because the expected recovery does not cover the human follow-up. <br>⚠️ *Hard to operate:* Patient data is regulated health information. Access, retention and business-associate obligations are the design constraint here, and they come before any modelling. <br>*Menu:* Claim × appeal path × effort × expected recovery <br>*Data:* Remittance and denial-code history, payer-specific appeal outcomes, effort per claim |
| **B2B receivables follow-up** | ⚪ Market blueprint | Small overdue invoices not worth human collection effort — first-party follow-up on your own ledger, not buying someone else's claims. <br>⚠️ *Hard to operate:* Chasing third-party consumer debt is a regulated activity in most jurisdictions and is a different market from managing your own ledger; see judgment and receivables purchasing under Flagged. <br>*Menu:* Invoice × contact sequence × timing × settlement offer <br>*Data:* Ageing and payment behaviour, dispute reasons, per-action recovery rates |
| **Tender and RFP bidding** | ⚪ Market blueprint | Opportunities firms never analyse because reading the tender costs more than the option is worth. The reject set here is created almost entirely by evaluation cost. <br>*Menu:* Tender × bid/no-bid × price × scope <br>*Data:* Published tenders and awards, historical win rates by category, delivery cost records |

## Flagged — do not operate without counsel

These have textbook menu structure, which is exactly why they are listed. They also carry legal, regulatory or platform-rule exposure. HyperC declines them under the API Terms; they are documented so nobody rediscovers them the expensive way.

| Market | State | Notes |
| --- | --- | --- |
| **Tax lien certificates** | ⛔ Separate perimeter | Perfect menu structure — and state-regulated, with long resolution horizons. Counsel first. |
| **Judgment and receivables purchasing** | ⛔ Separate perimeter | Collections law applies to the operator, not only to the seller. |
| **Event tickets** | ⛔ Separate perimeter | Resale is restricted or criminal depending on state and venue. Declined by policy. |
| **Reservation arbitrage** | ⛔ Separate perimeter | Outright banned in several cities. Declined by policy. |
| **Aged social accounts** | ⛔ Separate perimeter | Terms-of-service violation with account-death risk on both sides of the trade. |
| **Trademark and brand-name speculation** | ⛔ Separate perimeter | UDRP proceedings will eat the portfolio. Distinct from ordinary expiring-domain drops. |
| **Legal collections** | ⛔ Separate perimeter | Claims too small for conventional collection economics. Debt collection is a licensed, heavily supervised activity and HyperC declines it under the API Terms; listed so the structure is not rediscovered the expensive way. <br>*Menu:* Claim × action × cost × expected recovery <br>*Data:* Claim and judgment records, recovery outcomes |
| **Thin public equities** | ⛔ Separate perimeter | Small positions institutional investors cannot economically analyse. Securities: a separate regulatory perimeter, excluded from profit-share pricing and gated under the API Terms. <br>*Menu:* Security × position size × entry/exit <br>*Data:* Price and volume series, filings, liquidity measures |
| **Closed-end fund and ETF dislocations** | ⛔ Separate perimeter | Small temporary pricing discrepancies participants leave. Securities perimeter; listed as structure, not as an offer. <br>*Menu:* Fund × size × entry/exit window <br>*Data:* NAV and market price series, creation/redemption data, spread history |
| **Cross-venue short-lived arbitrage** | ⛔ Separate perimeter | Executable states that disappear before slower participants act. Quoted price alone is not the opportunity — size, liquidity, exit and impact usually dominate it. Financial perimeter. <br>*Menu:* Venue pair × size × latency budget <br>*Data:* Order-book snapshots, fee and settlement terms, realised slippage |

## Proposing a market

Members and enterprises propose markets continuously, and the catalogue is expected to
grow — several entries here started as a member's experiment. If you operate a market
that clears the four criteria, tell us: [hyperc.com/contact.html?topic=market](https://hyperc.com/contact.html?topic=market).

Maintained market workflows, weekly market drops and the skills that go with them are part
of the [P34 Membership](https://hyperc.com/membership.html).

*Catalogue version 2026-08-27. Regenerated from a single source; the website, this file and
`markets.json` are always in sync.*
