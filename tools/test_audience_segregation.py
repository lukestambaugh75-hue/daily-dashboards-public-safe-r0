import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = [
    ROOT / "index.html",
    ROOT / "styles.css",
    *sorted((ROOT / "dashboards").glob("*.html")),
]
FORBIDDEN_DEVIN_RUNTIME = (
    "kegerator-tracker-r0",
    "ps5-tv-deal-tracker-r0",
    "devin.mullen89@gmail.com",
)


class AudienceSegregationTests(unittest.TestCase):
    def test_public_safe_runtime_has_no_devin_surface_links(self):
        for path in RUNTIME_FILES:
            text = path.read_text(encoding="utf-8").lower()
            for forbidden in FORBIDDEN_DEVIN_RUNTIME:
                with self.subTest(path=path.name, forbidden=forbidden):
                    self.assertNotIn(forbidden, text)

    def test_hub_top_actions_and_top_picks_use_only_local_public_safe_views(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="dashboards/ford.html"', text)
        self.assertIn('href="dashboards/washer.html"', text)
        self.assertIn('href="dashboards/stroller.html"', text)
        self.assertIn("Raptor public-safe lead", text)
        self.assertIn("Washer checkout gate", text)
        self.assertIn("Nuna stroller price board", text)
        self.assertNotIn("Outdoor keg value", text)
        self.assertNotIn("PS5 and TV stack", text)

    def test_mobile_table_layout_is_bounded_to_the_hub_viewport(self):
        css = (ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertIn("table-layout: fixed", css)
        self.assertIn("overflow-wrap: anywhere", css)


if __name__ == "__main__":
    unittest.main()
