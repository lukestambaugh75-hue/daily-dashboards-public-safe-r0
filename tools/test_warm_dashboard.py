import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMBINED = ROOT / "dashboards" / "baby-stroller.html"


class WarmDashboardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = COMBINED.read_text(encoding="utf-8")

    def test_warm_decision_layer_is_present(self):
        self.assertIn("One calm view of what’s next.", self.text)
        self.assertIn("Worth looking at", self.text)
        self.assertIn("Our baby list · shared with Luke + Julie", self.text)
        self.assertIn('class="warm-combined"', self.text)

    def test_price_and_registry_metrics_are_visible(self):
        self.assertIn("Best new stroller price", self.text)
        self.assertIn("Registry verified", self.text)
        self.assertIn('class="warm-metric"', self.text)

    def test_detail_switch_is_semantic_and_not_cycle_only(self):
        self.assertIn('role="tablist"', self.text)
        self.assertGreaterEqual(self.text.count('role="tab"'), 2)
        self.assertIn('aria-selected="true"', self.text)
        self.assertIn("Stroller", self.text)
        self.assertIn("Baby gear", self.text)
        self.assertNotIn("Cycle details", self.text)

    def test_warm_surface_has_no_old_dark_combined_controls(self):
        self.assertNotIn("combined-price", self.text)
        self.assertNotIn("combined-switch", self.text)
        self.assertNotIn("#111214", self.text)


if __name__ == "__main__":
    unittest.main()
