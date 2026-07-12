import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMBINED = ROOT / "dashboards" / "baby-stroller.html"


class WarmDashboardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = COMBINED.read_text(encoding="utf-8")

    def test_spreadsheet_dashboard_has_all_three_sheets(self):
        self.assertIn("Stroller deals", self.text)
        self.assertIn("Baby registry", self.text)
        self.assertIn("Gear safety", self.text)
        self.assertIn('id="registry-panel"', self.text)
        self.assertIn('id="gear-panel"', self.text)

    def test_price_and_registry_metrics_are_visible(self):
        self.assertIn("Best new stroller", self.text)
        self.assertIn("Registry rows", self.text)
        self.assertIn("all reconciled rows", self.text)
        self.assertIn("Qty requested", self.text)
        self.assertIn("Qty purchased", self.text)

    def test_detail_switch_and_search_are_present(self):
        self.assertIn('role="tablist"', self.text)
        self.assertGreaterEqual(self.text.count('role="tab"'), 3)
        self.assertIn('aria-selected="true"', self.text)
        self.assertIn('id="previous-view"', self.text)
        self.assertIn('id="next-view"', self.text)
        self.assertIn('id="table-search"', self.text)
        self.assertIn("row.dataset.search", self.text)

    def test_registry_rows_have_detail_controls_and_offer_buttons(self):
        self.assertIn("View details", self.text)
        self.assertIn("detail-toggle", self.text)
        self.assertIn("registry-detail", self.text)
        self.assertIn("Open Amazon", self.text)
        self.assertIn("Walmart", self.text)
        self.assertIn("https://www.amazon.com/dp/", self.text)

    def test_old_frothy_surface_is_removed(self):
        self.assertNotIn("One calm view of what’s next.", self.text)
        self.assertNotIn("warm-combined", self.text)
        self.assertNotIn("Cycle details", self.text)


if __name__ == "__main__":
    unittest.main()
