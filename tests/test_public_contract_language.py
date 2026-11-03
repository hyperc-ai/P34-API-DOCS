"""Regression checks for the public free-tier and input-test contract.

Market licenses, the order book and the two accounts (area_docs §7.1-§7.3,
§10 #10, §11.4): the token wallet page documents the plan account and the
accumulating account and no longer states the monthly accrual as a current
rule; the Market Store API page carries every trading path of the hub's
endpoint list and the "no buyer is guaranteed" sentence; no public text sells
a copy or a license as an investment. Each money split and refusal code is the
hub's and the console's (decisions D6, D12, D15, D16, Q19: the review fixes of
HANDOFF-D3).
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
