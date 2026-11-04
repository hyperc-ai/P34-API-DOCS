"""Regression checks for the public free-tier and input-test contract.

Market licenses, the order book and the two accounts (area_docs §7.1-§7.3,
§10 #10, §11.4): the token wallet page documents the plan account and the
accumulating account and no longer states the monthly accrual as a current
rule; the Market Store API page carries every trading path of the hub's
endpoint list and the "no buyer is guaranteed" sentence; no public text sells
a copy or a license as an investment. Each money split and refusal code is the
hub's and the console's (decisions D6, D12, D15, D16, Q19: the review fixes of
HANDOFF-D3). The W6 fixes: no prose suggests a cash payout to come (Terms
§§5.5-5.7, 6.8); the robots' rules are the protocol's mode-1 RULES word for
word; the `buy` permission and the group price read as the hub's licenses
words; the 2026-12-21 callout is written before the date it names. Owner
decision 2026-11-04: the publisher terms hcb-publisher-2026-11 govern from
{L} = 2026-11-04 ({PUBLISHER_FROM}, Terms §5.7) and resale, direct offers and
authorship transfer are open from that day; only the plan-credit lapse keeps
{LAPSE_FROM} = 2026-12-21. Owner decision 2026-11-04 ("start the new process
today, and for older users the 21st"): an account whose paid plan begins on
or after 2026-11-04 lapses from the Usage Week beginning 2026-11-02 (its
`lapse_from` reads that week's start); the members who already had a paid plan on 2026-11-04 (the §6.5 notice) keep rolling over until {LAPSE_FROM}.
`lapse_from` is the account's own, and the pages state the rule in the
owner's canonical sentences.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TEXT = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
               *sorted((ROOT / "skills").glob("**/*.md"))]
API_EXAMPLES = [ROOT / "examples" / "client" / "example_client.py",
                ROOT / "examples" / "data" / "make_samples.py",
                *sorted((ROOT / "examples" / "data").glob("*.json")),
                ROOT / "examples" / "pytest" / "test_p34_api.py"]


class PublicContractLanguageTest(unittest.TestCase):

    def test_retired_metadata_is_absent(self):
        for path in PUBLIC_TEXT:
            text = path.read_text()
            self.assertNotIn("sponsored_simulation", text, path)
            self.assertNotIn("business_observed", text, path)
            self.assertNotIn("synthetic_full", text, path)
            self.assertNotIn("grounding_labelling_mode", text, path)

    def test_api_examples_do_not_use_retired_synthetic_market(self):
        for path in API_EXAMPLES:
            self.assertNotIn("synthetic_inventory", path.read_text(), path)

    def test_exact_free_market_refusal_is_documented(self):
        text = (ROOT / "docs" / "04-errors-and-checks.md").read_text()
        self.assertIn('detail.code: "free_markets_only"', text)
        self.assertIn(
            "free tier only supports select markets, including t5market.com.", text)
        self.assertNotIn("free_partner_required", text)

    def test_free_tier_client_language_is_market_neutral(self):
        paths = [ROOT / "README.md", ROOT / "docs" / "02-endpoints.md",
                 ROOT / "docs" / "04-errors-and-checks.md",
                 ROOT / "skills" / "p34-submit-and-monitor" / "SKILL.md",
                 ROOT / "skills" / "p34-interpret-results" / "SKILL.md"]
        forbidden = ("free-partner", "partner-market", "partner-supplied",
                     "non-partner")
        for path in paths:
            text = path.read_text().lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, text, path)

    def test_input_test_contract_is_explicit(self):
        text = (ROOT / "docs" / "02-endpoints.md").read_text()
        self.assertIn("every tier", text)
        self.assertIn("input parsing and validation", text)
        self.assertNotIn("full intake and grounding", text)

    def test_transport_boundary_is_explicit(self):
        text = (ROOT / "skills" / "p34-submit-and-monitor" / "SKILL.md").read_text()
        self.assertIn("https://api.hyperc.com/v1", text)
        self.assertIn("must never append `/fit` or `/result` to a", text)
        self.assertNotIn("A chat client with no shell", text)


def _flat(path: Path) -> str:
    """The page's text with every run of whitespace as one space, so a
    phrase matches across the page's line breaks."""
    return " ".join(path.read_text().split())


def _prose(path: Path) -> str:
    """The page's text outside its fenced code blocks, flattened as by
    `_flat`: an example quotes an answer as the hub serves it, the prose is
    the page's own words."""
    return " ".join(re.sub(r"(?ms)^```.*?^```", " ", path.read_text()).split())


def _unquoted(path: Path) -> str:
    """The page flattened as by `_flat`, with the "> " markers of its block
    quotes dropped, so a callout reads as one run of text."""
    return " ".join(re.sub(r"(?m)^> ?", "", path.read_text()).split())


# The owner's canonical sentences of 2026-11-04 for the plan-credit lapse, in
# the docs' ISO date style ("4 November 2026" -> 2026-11-04, "21 December
# 2026" -> 2026-12-21; the only adaptation allowed).
LAPSE_LONG = ("Unused plan credits lapse at the weekly refill. Members who "
              "already had a paid plan on 2026-11-04 keep the earlier rule until "
              "2026-12-21: until then their unused plan credits still move "
              "into their accumulating account.")
LAPSE_SHORT = ("unused ones lapse at the weekly refill (for members who already had a paid plan on 2026-11-04, from 2026-12-21)")
# the start of the Usage Week that holds 2026-11-04 (credit week 2965), from
# which an account whose paid plan begins on or after 2026-11-04 lapses
NEW_MEMBERS_LAPSE_FROM = "2026-11-02T00:00:00+00:00"
EARLIER_MEMBERS_LAPSE_FROM = "2026-12-21T00:00:00+00:00"


# The rules of GET /v1/agents/protocol from the licenses release on, as the
# hub's market_api_ref serves them in mode 1 (_RULES + _TRADING_WORDS["RULES"],
# after the AP2/D3-fix: an ask is never a "listing", area_docs §0.7). The page
# quotes them word for word; it only sets names in code type.
PROTOCOL_RULES = [
    "bring your own key: one key = one robot; the hub never issues one unasked "
    "and never shows one twice",
    "register once, recall thereafter: look for your kept note and POST "
    "/v1/agents/recall before inventing a new key",
    "describe yourself honestly: your member sees your agent, operator and "
    "purpose on the attach page before attaching",
    "never send the key anywhere but the Authorization header of this hub; the "
    "key id (first 20) is safe to quote",
    "propose, do not pay: your member pays your cart on its page — unless they "
    "gave you “Buy without asking”, and then only within their budget",
    "never write a card's earnings, proof, deploys or holders: they come from "
    "Business Builder reports, HyperC's assessor and what happened (the API "
    "refuses them: 422 read_only)",
    "a workspace address is a password: never put it in a note, a log, a card "
    "or a message",
    "analyse before you propose: bring your member a short, quantified "
    "proposal, never the raw store",
    "buy, sell and give only within your limits: your budget; your member's "
    "collections, minimum price and monthly cap — every ask and transfer is "
    "listed in an e-mail digest to your member",
    "money routes need an Idempotency-Key: repeat it only to retry the same "
    "request; after a definitive failure use a new one",
    "follow the market and your copies with the integer cursors "
    "(/v1/licenses/feed?after=, /v1/licenses/moves?after=, "
    "/v1/agents/events?cursor=), never with a timestamp",
    "a direct offer waits for its recipient; its receipt — or "
    "/v1/licenses/moves — is the proof that copies moved",
    "a master key manages keys only within its own permissions, collections, "
    "limits and budget; it never makes another master and never moves "
    "authorship",
]


def _quoted_rules(path: Path) -> list[str]:
    """The bullets under the page's "## Rules for robots", code type
    removed, each flattened to one line."""
    text = path.read_text()
    section = text[text.index("## Rules for robots"):]
    section = section[:section.index("\n\nThe last five rules")]
    items = re.split(r"(?m)^- ", section)[1:]
    return [" ".join(item.replace("`", "").split()) for item in items]


# The Market Store API paths of the licenses release, as the hub's endpoint
# list (market_api_ref.ENDPOINTS) spells them: the groups "Trading" and
# "Copies and offers", the app's inventory push, the member's keys, the
# family read, a version's description and the publisher terms.
TRADING_ENDPOINTS = [
    ("GET", "/v1/licenses/book/{id}"),
    ("GET", "/v1/licenses/feed"),
    ("GET", "/v1/licenses/series/{id}"),
    ("POST", "/v1/licenses/orders"),
    ("GET", "/v1/licenses/orders"),
    ("GET", "/v1/licenses/orders/{id}"),
    ("POST", "/v1/licenses/asks"),
    ("GET", "/v1/licenses/asks"),
    ("GET", "/v1/licenses/asks/{id}"),
    ("PATCH", "/v1/licenses/asks/{id}"),
    ("DELETE", "/v1/licenses/asks/{id}"),
    ("POST", "/v1/licenses/checks"),
    ("GET", "/v1/licenses/checks/{id}"),
    ("GET", "/v1/licenses/mine"),
    ("GET", "/v1/licenses/moves"),
    ("POST", "/v1/licenses/offers"),
    ("GET", "/v1/licenses/offers"),
    ("POST", "/v1/licenses/offers/mute"),
    ("GET", "/v1/licenses/offers/{id}"),
    ("POST", "/v1/licenses/offers/{id}/accept"),
    ("POST", "/v1/licenses/offers/{id}/decline"),
    ("POST", "/v1/licenses/offers/{id}/cancel"),
    ("GET", "/v1/me/installs"),
    ("POST", "/v1/me/installs/{id}/retire"),
    ("DELETE", "/v1/me/installs/{id}/retire"),
    ("POST", "/v1/app/inventory"),
    ("POST", "/v1/me/agents"),
    ("GET", "/v1/me/agents/changes"),
    ("GET", "/v1/me/agents/{id}"),
    ("GET", "/v1/research/cards/{id}/family"),
    ("PUT", "/v1/cards/{id}/versions/{n}/notes"),
    ("GET", "/v1/store/publisher-terms"),
]

# The fixed sentences of area_docs §3.2 the trading section reuses verbatim.
FIXED_SENTENCES = {
    "S4": "The price shown is the best you can get now: the cheapest copy for "
          "sale or the author's price for you, whichever is lower. At the same "
          "price, the copy for sale is sold first.",
    "S5": "HyperC keeps 30 % of a new license and 10 % of a resale, at least 1 "
          "cent on each priced sale; the rest goes to the seller's "
          "accumulating account. Giving a copy away is free.",
    "S6": "When you buy a new license and pick a version from a fork, 5 % of "
          "the price goes to that fork's author, out of the original author's "
          "70 %.",
    "S7": "The author gets nothing from resales: a resale pays the reseller.",
    "S9": "Past prices are history, not a forecast. A market's price can fall "
          "as well as rise, and nobody is guaranteed a buyer.",
    "S10": "Trades and transfers are final. HyperC support can reverse a "
           "purchase only while that copy is still untouched with its buyer.",
}


class MarketLicensesLanguageTest(unittest.TestCase):

    def test_token_wallet_documents_the_plan_and_accumulating_accounts(self):
        text = _flat(ROOT / "docs" / "06-token-wallet.md")
        self.assertTrue(text.startswith(
            "# 6. Token wallet: the plan account, the accumulating account, "
            "transfers and the ledger"))
        for phrase in ("plan account", "accumulating account", "lapse",
                       "Usage Week beginning 2026-12-21", "`accounts`",
                       "`account_part`", "`reversal_debt`", "`lapse_from`",
                       "`accounts.accumulating.balance` equals `balance`; "
                       "`plan` is still the plan code."):
            self.assertIn(phrase, text)
        self.assertNotIn("credited every month", text)
        self.assertNotIn("Every monthly window", text)
        self.assertNotIn("{LAPSE_FROM}", text)

    def test_the_monthly_accrual_is_not_a_current_rule_anywhere(self):
        stale = ("credited every month", "Every monthly window",
                 "unused tokens accumulate", "Monthly token accruals scale",
                 "monthly accruals that carry over",
                 "no active subscription — subscribe to a plan")
        for path in (ROOT / "README.md", ROOT / "docs" / "02-endpoints.md",
                     ROOT / "docs" / "06-token-wallet.md"):
            text = _flat(path)
            for phrase in stale:
                self.assertNotIn(phrase, text, path)
        endpoints = _flat(ROOT / "docs" / "02-endpoints.md")
        self.assertIn("Every calculation is paid from your plan account (this "
                      "week's plan credits) first, then your accumulating "
                      "account (the token balance)", endpoints)

    def test_market_store_api_documents_every_trading_path(self):
        text = _flat(ROOT / "docs" / "12-market-store-api.md")
        for method, path in TRADING_ENDPOINTS:
            self.assertIn(path, text, (method, path))
            route = (re.escape(method) + r" (?:https://api\.hyperc\.com)?"
                     r"(?:/hub)?" + re.escape(path))
            self.assertTrue(re.search(route, text), (method, path))
        self.assertIn("## Trading: copies, the order book, offers", text)
        self.assertIn("None of them is a promise that a business will make "
                      "money for the next operator, or that a copy will find "
                      "a buyer at any price.", text)

    def test_trading_section_reuses_the_fixed_sentences(self):
        text = _flat(ROOT / "docs" / "12-market-store-api.md")
        section = text[text.index("## Trading: copies, the order book, offers"):
                       text.index("## Payouts")]
        for name, sentence in FIXED_SENTENCES.items():
            self.assertIn(sentence, section, name)
        # an ask is never a "listing": that word is a card's publication state
        self.assertIsNone(re.search(r"\blisting", section))

    def test_fork_royalty_is_never_limited_to_the_copy_in_use(self):
        for path in PUBLIC_TEXT:
            text = _flat(path).lower()
            self.assertNotIn("the copy the buyer will use", text, path)
            self.assertNotIn("the copy you run", text, path)

    def test_each_split_is_the_fee_of_its_sale_type(self):
        # D12/D16: a priced offer of new licenses and a priced authorship
        # offer pay the new-license fee, only a holder's copy the resale fee;
        # D6/D15: a resold copy pays no fork royalty; Q19: a refund's plan
        # part beyond this week's use lapses, it never reaches the balance
        text = _flat(ROOT / "docs" / "12-market-store-api.md")
        self.assertNotIn("each resale or priced direct offer books 90 %", text)
        self.assertIn("each resale, or a member's priced direct offer of "
                      "copies they hold, books 90 % to its seller", text)
        self.assertIn("a priced authorship offer books 70 % to the former "
                      "author", text)
        self.assertIn("when the line buys a new license; a resold copy pays "
                      "none", text)
        wallet = _flat(ROOT / "docs" / "06-token-wallet.md")
        self.assertIn("a plan part beyond that lapses: it never reaches the "
                      "balance", wallet)

    def test_order_refusals_name_their_codes(self):
        text = _flat(ROOT / "docs" / "12-market-store-api.md")
        self.assertIn('fill: "all", pay?: "credits"}', text)
        self.assertIn('`credits_only` (a `pay` other than `"credits"`)', text)
        self.assertIn("(the hourly order caps answer `429 too_many_purchases` "
                      "with `Retry-After`)", text)

    def test_no_prose_promises_a_cash_payout_to_come(self):
        # Terms §5.5 ("spendable Tokens, not a cash payout"), §5.6 (no cash
        # value), §6.8; the website says "Cash payouts are not offered."
        # The JSON example of GET /v1/payouts keeps the note the hub serves.
        for path in PUBLIC_TEXT:
            prose = _prose(path).lower()
            self.assertNotIn("payouts are not offered yet", prose, path)
            self.assertNotIn("while none are offered", prose, path)
        payouts = _prose(ROOT / "docs" / "12-market-store-api.md")
        self.assertIn("**Cash payouts are not offered**: proceeds are "
                      "spendable credits (`cash.live` is `false` and "
                      "`cash.payouts` is empty); credits never convert to "
                      "cash", payouts)

    def test_rules_for_robots_are_the_protocols_word_for_word(self):
        rules = _quoted_rules(ROOT / "docs" / "12-market-store-api.md")
        self.assertEqual(rules, PROTOCOL_RULES)
        self.assertTrue(all(not re.search(r"\blisting", r) for r in rules))

    def test_buy_and_group_price_read_as_the_licenses_words(self):
        # agents.PERMISSIONS["buy"] under the licenses; a group price at or
        # above the public one buys a transferable first copy (D11, cf449d0)
        text = _flat(ROOT / "docs" / "12-market-store-api.md")
        self.assertIn("| `buy` | Buy without asking | **off** | pay for cards "
                      "— its cart, orders in the order book and priced offers "
                      "made to the holder — from the holder's credits at once, "
                      "within the monthly budget and the per-card ceiling |",
                      text)
        self.assertNotIn("pay cards of its cart", text)
        self.assertIn("A group price covers the holder's first copy only; that "
                      "copy is personal when the group's price is below the "
                      "public price.", text)
        self.assertNotIn("first copy only, and that copy is personal", text)

    def test_the_lapse_callout_is_written_before_its_date(self):
        # the page ships on 2026-11-04, 47 days before the earlier members'
        # lapse and on the day of the new members' one (the callouts are a
        # block quote: its "> " markers are dropped)
        wallet = _unquoted(ROOT / "docs" / "06-token-wallet.md")
        self.assertIn("**Changed 2026-11-04.** For an account whose paid plan "
                      "begins on or after 2026-11-04, unused plan credits "
                      "lapse at the end of their Usage Week, from the week "
                      "that began on 2026-11-02: the first refill at which "
                      "they lapse is the one of 2026-11-09 00:00 UTC. "
                      "`lapse_from` is "
                      "now the account's own.", wallet)
        self.assertIn("**Changes 2026-12-21.** From 2026-10-21 until "
                      "2026-12-21, the unused plan credits of members who "
                      "already had a paid plan on 2026-11-04 move into the token "
                      "balance at the end of their week (ledger kind `grant`, "
                      "from `plan-rollover`). From the week starting "
                      "2026-12-21 they lapse again. Tokens already on the "
                      "balance stay; nothing is restated.", wallet)
        self.assertNotIn("**Changed 2026-12-21.**", wallet)
        self.assertNotIn("**Changes 2026-11-04.**", wallet)

    def test_the_wallet_states_the_lapse_in_the_owners_words(self):
        # owner decision 2026-11-04: new paid members lapse now, the members
        # who already had a paid plan on 2026-11-04 from 2026-12-21; the plan
        # account's paragraph and the lapse section say it in the long
        # sentence, word for word
        path = ROOT / "docs" / "06-token-wallet.md"
        text = _flat(path)
        self.assertGreaterEqual(text.count(LAPSE_LONG), 2)
        self.assertIn("### The weekly lapse Unused plan credits lapse at the "
                      "weekly refill.", text)
        self.assertIn("Nothing that has already moved into the accumulating "
                      "account is taken back.", text)
        self.assertIn("(§§1.25, 6.1, with the notice of §6.5)", text)
        # the rule of the day before the decision: one date for everyone
        for stale in ("Credits left in it at the refill lapse",
                      "Until the Usage Week beginning 2026-12-21, unused plan "
                      "credits still carry over",
                      "The weekly lapse from 2026-12-21",
                      "(every week before 2026-12-21, on every plan",
                      "carry-overs before 2026-12-21",
                      "carried over before 2026-12-21",
                      "the first week whose unused plan credits lapse:"):
            self.assertNotIn(stale, text)

    def test_lapse_from_is_documented_per_account(self):
        # plan_credits.lapse_from and accounts.plan.lapse_from are the
        # account's own: the start of week 2965 for a paid plan begun on or
        # after 2026-11-04, the start of week 2972 for an earlier member
        text = _prose(ROOT / "docs" / "06-token-wallet.md")
        self.assertIn("`lapse_from` is the account's own: when the lapse "
                      "starts for this account — the start of its first "
                      "lapsing week as an ISO time "
                      f"(`{EARLIER_MEMBERS_LAPSE_FROM}` for a member who already had a paid plan on 2026-11-04, "
                      f"`{NEW_MEMBERS_LAPSE_FROM}` for an account whose paid "
                      "plan began on or after 2026-11-04), `\"always\"` when "
                      "every week lapses, or `null` while every week carries "
                      "over.", text)
        self.assertIn("Its `lapses` and `lapse_from` are those of "
                      "`plan_credits` above: this account's own rule, which "
                      "can differ from another account's in the same week.",
                      text)
        self.assertIn("for an account whose paid plan began on or after "
                      "2026-11-04, no week)", text)
        self.assertIn('like every week of its plan — reads `"accumulates": '
                      'false`, `"lapses": true` and `"lapse_from": '
                      f'"{NEW_MEMBERS_LAPSE_FROM}"`.', text)
        # the example is an earlier member's first lapsing week, and its two
        # lapse_from fields agree
        wallet = (ROOT / "docs" / "06-token-wallet.md").read_text()
        example = wallet[wallet.index("## `GET /account/balance`"):]
        example = example[example.index("```json"):]
        example = example[:example.index("\n```\n", 1)]
        self.assertEqual(example.count(f'"lapse_from": '
                                       f'"{EARLIER_MEMBERS_LAPSE_FROM}"'), 2)
        self.assertIn("An example — a founding member who already had a paid plan on 2026-11-04, partway through the Usage Week "
                      "beginning 2026-12-21", _flat(ROOT / "docs" /
                                                    "06-token-wallet.md"))

    def test_the_lapse_day_is_never_everyones(self):
        # 2026-12-21 is the lapse of the members who already had a paid plan on
        # 2026-11-04 only: in the prose of the wallet page and the README,
        # every mention of it names those members nearby
        for path in (ROOT / "README.md", ROOT / "docs" / "06-token-wallet.md"):
            text = " ".join(re.sub(r"(?m)^> ?", "", re.sub(
                r"(?ms)^```.*?^```", " ", path.read_text())).split())
            found = list(re.finditer(r"2026-12-21|21 December 2026", text))
            self.assertTrue(found, path)
            for m in found:
                window = text[max(0, m.start() - 450):m.end() + 300]
                self.assertIn("paid plan on 2026-11-04", window,
                              (path, window))

    def test_readme_states_the_lapse_in_the_short_words(self):
        readme = _flat(ROOT / "README.md")
        self.assertIn("The plan account holds the weekly plan credits, spent "
                      "first and refilled every Monday; " + LAPSE_SHORT + ".",
                      readme)

    def test_no_link_to_the_retired_lapse_anchor(self):
        # the lapse section is "### The weekly lapse" (#the-weekly-lapse)
        # since it holds both dates
        for path in PUBLIC_TEXT:
            self.assertNotIn("#the-weekly-lapse-from-2026-12-21",
                             path.read_text(), path)
        wallet = (ROOT / "docs" / "06-token-wallet.md").read_text()
        self.assertIn("\n### The weekly lapse\n", wallet)
        self.assertIn("(#the-weekly-lapse)", wallet)

    def test_publisher_terms_govern_from_the_notice_day(self):
        # {PUBLISHER_FROM} = {L} = 2026-11-04 by owner decision (no longer
        # {LAPSE_FROM}): the store page names the day the 2026-11 publisher
        # terms govern every priced market, and 2026-12-21 (the lapse) is
        # never a date of the publisher terms or of trading anywhere
        store = _flat(ROOT / "docs" / "12-market-store-api.md")
        self.assertIn("from 2026-11-04 the 2026-11 publisher terms govern "
                      "every priced market whatever label was recorded",
                      store)
        self.assertNotIn("2026-12-21", store)
        trading = re.compile(r"publisher|resale|resell|direct offer|"
                             r"authorship|order book|\btrad(?:e|es|ing)\b")
        for path in PUBLIC_TEXT:
            text = _flat(path)
            for m in re.finditer(r"2026-12-21|21 December|December 21", text):
                window = text[max(0, m.start() - 200):m.end() + 200]
                self.assertIsNone(trading.search(window.lower()),
                                  (path, window))

    def test_no_public_text_sells_copies_as_an_investment(self):
        near = re.compile(r"\bcop(?:y|ies)\b|\blicen[cs]e")
        for path in PUBLIC_TEXT:
            text = _flat(path).lower()
            for m in re.finditer(r"investment|returns on your copies|appreciat",
                                 text):
                window = text[max(0, m.start() - 200):m.end() + 200]
                self.assertIsNone(near.search(window), (path, window))


if __name__ == "__main__":
    unittest.main()
