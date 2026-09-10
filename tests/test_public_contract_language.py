"""Regression checks for the public free-tier and input-test contract."""

from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
