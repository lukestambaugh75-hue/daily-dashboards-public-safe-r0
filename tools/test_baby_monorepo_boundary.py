import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BabyMonorepoBoundaryTests(unittest.TestCase):
    def test_publisher_does_not_read_private_pregnancy_or_daycare_projects(self):
        publisher = (ROOT / "tools/publish_dashboards.py").read_text(encoding="utf-8")
        self.assertNotIn("projects/daycare-research", publisher)
        self.assertNotIn("projects/pregnancy-copilot", publisher)

    def test_public_pages_do_not_expose_private_project_paths_or_cost_handoff(self):
        forbidden = (
            "projects/daycare-research",
            "projects/pregnancy-copilot",
            "approved_monthly_cost_usd",
            "approved-cost-input.json",
        )
        pages = [ROOT / "index.html", *sorted((ROOT / "dashboards").glob("*.html"))]
        self.assertTrue(pages)
        for page in pages:
            text = page.read_text(encoding="utf-8")
            for value in forbidden:
                with self.subTest(page=page.name, value=value):
                    self.assertNotIn(value, text)


if __name__ == "__main__":
    unittest.main()
