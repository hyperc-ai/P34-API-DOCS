# 10. P34 Applicability Assessment

Assess the constructed P34 business pipeline and the `business_description`
provided to P34 against this checklist before submitting a fit. Fix failures
and investigate unverified requirements before the dependent submission. You
may ask the user to change the initial business description or business type
to meet the requirements or improve the prospect of an operational, profitable
business on the selected market.

Keep the levels below explicit: **Must hold** is required, **Highly
recommended** is a recommendation, and **Note** explains an implication.
Conditional requirements apply when the construction uses that mechanism.
Record the evidence and scope for every item, including recommendations and
the reason a conditional item does not apply. Declare applicability only when
all applicable required checks pass; disclose any unmet recommendation.

This assessment concerns the business construction. The API's format checks
and fit-time requirements remain documented in
[Errors and checks](04-errors-and-checks.md). An accepted request does not
establish applicability, and applicability does not demonstrate profitability.

## Checklist

1. **Must hold — Executable business instrument.** Define what each option in
   the business menu commits the business to do, its feasible size, costs,
   predetermined investment horizon (for example, four weeks of sales or
   liquidation), closing policy, replayed write-off after the time limit, and
   cash-return mechanism. Menus, quantities, and Sales must describe the same
   operation. A constructed instrument must be operationally feasible and
   economically meaningful.

2. **Highly recommended — Natural unobserved outcomes.** Establish from source
   records why some feasible alternatives have unknown realized outcomes.
   Missingness must arise from the operation or constructed instrument: an
   offer not taken, an unexecuted contingent process, unavailable
   counterfactual fills, or another genuine observation limit. Preserve known
   outcomes; masking records or inventing uncertainty does not establish
   applicability. If the originally proposed market has fully observed
   outcomes, check whether an economically meaningful business process can be
   constructed through size or capacity commitments, market-making,
   contingent multi-leg execution, customer acquisition, bundling,
   transformation, or alternative contract terms, such that profit depends
   on customer, counterparty, or operational responses that cannot be
   reconstructed for unexecuted alternatives. Added complexity or combinations
   of fully observable payoffs alone do not establish missingness.

3. **Must hold — Naturally biased observed outcomes and historical menus
   covering the deployment distribution.** Unobserved outcomes produce biased
   observation. This is normal, and P34 is designed for these situations. To
   account for that bias, P34 must receive the full options menu historically
   and at task time. Historical menus can have unknown outcomes, but their
   selection of options must cover the deployment distribution: each menu
   should represent what the task menu would have been at that past decision
   time. Occasional incomplete menus are acceptable only when history still
   contains menus of varying completeness approaching deployment menu sizes.
   Report those departures. It is highly recommended that every historical
   menu cover the deployment distribution exactly.

4. **Note — Extrapolation without compulsory exploration.** Applicability does
   not require an unbiased sample, paid random trades, deliberately
   loss-making trades to obtain missing labels, or any specific exploratory
   trade before the P34 fit.

5. **Must hold — Substantial genuine choice.** Require at least **100
   economically distinct feasible configurations** per assessed historical
   and task menu; target **1,000 or more** where supported by the operation.
   Count configurations separately from quantity variants, duplicate rows,
   and expired opportunities. If historical menus contain too few genuine
   configurations, expand the filter or sourcing, or enhance the instrument
   to create more genuine portfolio opportunities. P34 assembles portfolios
   from current opportunities. In some constructions, windowing can add past
   and expired trades as scoring context, so a current trade is assessed
   against that portfolio. Exclude past trades at execution and report the
   currently executable count separately; context cannot inflate that count.
   See item 14.

6. **Must hold — Complete source coverage.** Supply P34 with all available
   information for the assessed operation. Withholding data deteriorates
   performance. Carry decision-time information into inputs and later
   execution and settlement information into outcome records, as required by
   item 8. Record source coverage and any unavailable data explicitly.

7. **Must hold — Faithful opportunity sets.** Reconstruct the alternatives
   actually available at each decision time using explicit eligibility rules.
   Preserve feasible unattractive and unchosen alternatives. Apply clustering
   and eligibility without outcome hindsight. Eligibility rules must stay the
   same across historical menus and the task menu.

8. **Must hold — Decision-time integrity.** Restrict menu inputs and features
   to information available at the decision cutoff. Keep later execution and
   settlement information in the outcome record or `profit` column. Apply
   identical feature definitions to historical and task menus, with explicit
   timestamps, time zones, availability delays, and settlement horizons. Task
   rows remain prediction targets with blank `profit`, as required by the
   [data contract](03-data-format.md#the-menus-table).

9. **Must hold — Natural quantity.** Define quantity in executable units of
   exposure, inventory, capacity, or deal size, with valid increments and
   limits. Establish how each quantity changes the underlying action and its
   resource use. Quantity must represent a business choice rather than a row
   count or an arbitrary confidence multiplier. Provide this definition in
   the `business_description` input to P34.

10. **Must hold — Coherent volume response.** Define how quantity changes
    committed exposure, available inventory or capacity, and the volume
    eligible for execution or sale. Verify that reductions constrain the
    corresponding volume under the declared allocation rule. Preserve valid
    proportional scaling and state assumptions behind monotonicity.
    Distinguish these known constraints from uncertain realized fills, sales,
    and profit; preserve original observations and label resized
    reconstructions explicitly. Using quantity or volume to implement mutexes
    or other non-scalable concepts is prohibited. The documented grouping of
    alternative sizes is separate from external business exclusivity; see
    item 15 and [one choice per key-date](03-data-format.md#one-choice-per-key-date-qty-and-cost-are-mutually-exclusive).

11. **Must hold — Complete economic accounting.** Define net profit, currency,
    and accounting basis consistently across Menus and Sales. Include
    acquisition, transport, holding or storage, financing, insurance, fees,
    slippage, returns, and exit or disposal costs as applicable, including
    costs accrued over the holding and closeout periods. Reconcile proceeds,
    terminal value, and costs without double-counting acquisition losses or
    write-offs. Identify estimates and unsettled obligations explicitly.

12. **Must hold — Predetermined investment horizon.** Fix the clock-start
    event, holding duration, and permitted early exits before observing
    outcomes; apply the same rules to historical and task options. Apply
    write-off or liquidation rules. Record all observed profits over this
    defined investment period and its declared terminal treatment. For quick
    Amazon resale from a US supplier, **6–8 weeks is an illustrative range**;
    choose a specific duration for the instrument. Faster assets may require
    shorter periods.

13. **Must hold — Terminal liquidation or write-off.** Predetermine and apply
    a liquidation or write-off mechanism to remaining inventory or exposure
    at expiry, with a bounded closeout or settlement interval, costs,
    residual-value rule, and failed-liquidation fallback. Distinguish realized
    proceeds from policy-defined accounting values; a write-off is not a
    sale. Preserve and separately reconcile later recoveries, refunds, or
    charges; never extend the holding period retrospectively to improve
    profit.

14. **Must hold, if required by construction — Explicit streaming context.**
    When a live window is too small, define a reproducible rule for including
    past opportunities as scoring context. Score the intended combined
    volume, then identify genuinely new, currently executable candidates
    using persistent event identity and a recorded cutoff. Historical
    context must remain distinguishable from present choices and cannot
    inflate their reported count. Use the documented table contract; this
    checklist introduces no new API flag or execution capability for context.

15. **Must hold, if required by construction — External business mutexes.**
    Keep business-level exclusivity and shared-resource constraints outside
    unsupported API semantics, separate from documented quantity grouping.
    Fit on the faithful history. Resolve conflicts after prediction using a
    declared rule; random resolution must use a recorded seed and draw
    policy. Report the resulting executable portfolio separately from P34's
    returned selection and profit prediction.

16. **Must hold, if required by construction — Coherent alternative
    universes.** If conflicts are handled through separate menu and Sales
    sets, define each universe by an operationally meaningful rule fixed
    before outcomes are inspected. Apply that rule consistently to history
    and task data, preserve relevant alternatives across the universes, and
    document overlaps. Compare predictions on a common economic basis and
    resolve cross-universe conflicts externally.

17. **Must hold — Evidence-based applicability decision.** Record each
    requirement as **PASS**, **FAIL**, or **UNVERIFIED**, with supporting
    evidence and a concrete remedy for gaps. Declare applicability only when
    all applicable requirements pass; an untested later stage remains
    unverified. Report source completeness, evidence of selection and
    observation bias, genuine choice counts, observed and unknown outcomes,
    sizing behavior, the extent and causes of unobserved-size uncertainty,
    investment horizon, and terminal policy. Keep **applicability**, **API
    acceptance**, and **demonstrated profitability** as separate conclusions.

## Assessment record

Keep the assessment with the prepared request and its business description.
For each numbered item, record its level, whether its condition applies,
status, evidence references, and remedy. For conditional checks, document the
construction that triggers the check or the evidence that it does not apply.
An intended future implementation is not evidence of a passing check.

Report per-menu genuine configuration counts separately from quantity-option
rows and historical scoring context. Describe the assessed source and time
coverage, any incomplete menus, known and unknown outcomes, and why size
counterfactuals are unobserved. Record the horizon and terminal policy used by
the labels and predictions. Reassess when the construction, eligibility,
sources, sizing, horizon, or execution policy changes.

Fix required failures before submission. Resolve an unverified applicable
requirement with evidence, or report the dependent submission as blocked.
Keep recommendations visible without silently making them compulsory. API
acceptance and observed profitable operation each need their own evidence;
neither follows from passing this checklist.
